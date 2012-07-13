import sys

import wsgiref.handlers
import xml.etree.cElementTree as ET
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext.db import polymodel

import logging


data_models = []

class Link(db.Model):
    site = db.StringProperty()
    title = db.StringProperty()
    url = db.LinkProperty()
    description = db.TextProperty()
    
class FullAddress(db.Model):
    address = db.StringProperty()
    city = db.StringProperty()
    state = db.StringProperty()
    country = db.StringProperty()
    zip_ = db.StringProperty()
    
class ContactInfo(db.Model):
    phone = db.PhoneNumberProperty()
    email = db.EmailProperty()
    #mail = FullAddress()
    mail = db.ReferenceProperty(FullAddress)
    
class HumanImpact(db.Model):
    deaths = db.IntegerProperty()
    displaced = db.IntegerProperty()
    injured = db.IntegerProperty()
    missing = db.IntegerProperty()
    misc = db.StringProperty()

class EconomicImpact(db.Model):
    amount = db.IntegerProperty()
    currency = db.StringProperty()
    misc = db.StringProperty()
    
class Impact(db.Model):
    #human = HumanImpact()
    #economic = EconomicImpact()
    human = db.ReferenceProperty(HumanImpact)
    economic = db.ReferenceProperty(EconomicImpact)
    
class Location(db.Model):
    city = db.StringProperty()
    region = db.StringProperty()
    country = db.StringProperty()

class Date(db.Model):
    time = db.StringProperty()
    day = db.IntegerProperty()
    month = db.IntegerProperty()
    year = db.IntegerProperty()
    misc = db.StringProperty()
    
class CrisisInfo(db.Model):
    history = db.TextProperty()
    help = db.StringProperty()
    resources = db.StringProperty()
    type_ = db.StringProperty()
    #time = Date()
    #loc = Location()
    #impact = Impact()
    time = db.ReferenceProperty(Date)
    loc = db.ReferenceProperty(Location)
    impact = db.ReferenceProperty(Impact)
    
class OrgInfo(db.Model):
    type_ = db.StringProperty()
    history = db.TextProperty()
    #contact = ContactInfo()
    #loc = Location()
    contact = db.ReferenceProperty(ContactInfo)
    loc = db.ReferenceProperty(Location)

class PersonInfo(db.Model):
    type_ = db.StringProperty()
    #birthdate = Date()
    birthdate = db.ReferenceProperty(Date)
    nationality = db.StringProperty()
    biography = db.TextProperty()
    
class Reference(db.Model):
    #primaryImage = Link()
    primaryImage = db.ReferenceProperty(Link)
    #images = []
    #videos = []
    #socials = []
    #exts = []
    images = db.ListProperty(db.Key)
    videos = db.ListProperty(db.Key)
    socials = db.ListProperty(db.Key)
    exts = db.ListProperty(db.Key)
    
class Crisis(db.Model):
    idref = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    #info = CrisisInfo()
    #ref = Reference()
    info = db.ReferenceProperty(CrisisInfo)
    ref = db.ReferenceProperty(Reference)
    misc = db.StringProperty()
    #relatedOrgs = []#db.ListProperty(db.ReferenceProperty(Organization))
    #relatedPeople = []#db.ListProperty(db.ReferenceProperty(Person))
    relatedOrgs = db.ListProperty(db.Key)
    relatedPeople = db.ListProperty(db.Key)

class Organization(db.Model):
    idref = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    #info = OrgInfo()
    #ref = Reference()
    info = db.ReferenceProperty(OrgInfo)
    ref = db.ReferenceProperty(Reference)
    misc = db.StringProperty()
    #relatedCrises = []#db.ListProperty(db.ReferenceProperty(Crisis))
    #relatedPeople = []#db.ListProperty(db.ReferenceProperty(Person))
    relatedCrises = db.ListProperty(db.Key)
    relatedPeople = db.ListProperty(db.Key)
    
class Person(db.Model):
    idref = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    #info = PersonInfo()
    #ref = Reference()
    info = db.ReferenceProperty(PersonInfo)
    ref = db.ReferenceProperty(Reference)
    misc = db.StringProperty()
    #relatedCrises = []#db.ListProperty(db.ReferenceProperty(Crisis))
    #relatedOrgs = []#db.ListProperty(db.ReferenceProperty(Organization))
    relatedCrises = db.ListProperty(db.Key)
    relatedOrgs = db.ListProperty(db.Key)

class WorldCrises(db.Model):
    #crises = []#db.ListProperty(Crisis)
    #orgs = []#db.ListProperty(Organization)
    #people = []#db.ListProperty(Person)
    crises = db.ListProperty(db.Key)
    orgs = db.ListProperty(db.Key)
    people = db.ListProperty(db.Key)
    
    
class MainHandler(webapp.RequestHandler):
    def get(self):
        """
        This method is called by the GAE when a user navigates to the root page.
        It draws the page.
        """
        path = self.request.path

        crises = Crisis.all().fetch(50)
        orgs = Organization.all().fetch(50)
        people = Person.all().fetch(50)    
   
        #crises = data_models['crises'].values()
        #orgs = data_models['orgs'].values()
        #people = data_models['people'].values() 

        template_values = {
            'crises': crises,
            'people': people,
            'orgs': orgs,
        }

        self.response.headers['Content-Type'] = 'text/html'

        if path.startswith("/crises/") :
            self.response.out.write("crisis page yet to be implemented")
        elif path.startswith("/organizations/") :
            self.response.out.write("org page yet to be implemented")
        elif path.startswith("/people/"):
            self.response.out.write("person page yet to be implemented")
        else:
            self.response.out.write(str(template.render('djangogoodies/maintemplate.html', template_values)))
            #inFile = open("htmlgoodies/mockup.html", 'r')
            #outstr = inFile.read() #"HELLO CAR RAMROD"
            #inFile.close()
            #self.response.out.write(outstr)

class ExportHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(ExportXml(data_models))

class ImportFormHandler(webapp.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/import_upload')
        self.response.out.write('<html><body><table align="center" width="100%" height="100%"><tr height="200"><td></td></tr>')
        self.response.out.write('<tr><td><form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
        self.response.out.write('''Upload File: <input type="file" name="file"><br> <input type="submit"
            name="submit" value="Submit"> </form></td></tr><tr height="200"><td></td></tr></table></body></html>''')


class ImportUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        try:
            global data_models
            xml_file = self.get_uploads('file')[0].open()
            debug("XML_FILE: "+ str(xml_file))
            data_models = import_file(xml_file)
            debug("DATA_MODELS: " + str(data_models))
            self.response.out.write("Data was successfully imported")
            self.response.out.write("<script type=\"text/javascript\">")
            self.response.out.write("function RefreshParent(){parent.location.reload();}")
            self.response.out.write("</script>")
            self.response.out.write("<body onload=\"RefreshParent();\">")
        except:
            self.response.out.write("Please provide a valid XML file")
            
            
# ---------
# ImportXml
# ---------
def ImportXml(filename):
    """
    Imports data from an xml instance and saves it in heap
    Assumes valid xml instance
    filename the name of the .xml file
    return the desired data in multi-dimensional dictionary
    """
    return import_file(open(filename, "r"))

# ----
# pick
# ----

def pick(e):
    """
    Replaces an empty(None) element with an empty string
    """
    return "" if e is None else e.text

# -----
# pickn
# -----

def pickn(e):
    """
    Replaces an empty(None) element with a zero
    """
    return 0 if e is None else int(e.text)
    
# -----------
# import_file
# -----------
def import_file(xml_file):
    tree = ET.ElementTree(file = xml_file)
    root = tree.getroot()
    
    data = []
    
    crises = root.findall("crisis")
    for crisis in crises: 
        crisis_model = Crisis(key_name = crisis.attrib["id"], 
                              idref = crisis.attrib["id"], 
                              name = crisis.find("name").text)
                              
        info = crisis.find("info")
        info_model = CrisisInfo(history = pick(info.find("history")), 
                                help = pick(info.find("help")), 
                                resources = pick(info.find("resources")), 
                                type_ = pick(info.find("type")))
                                
        time = info.find("time")
        time_model = Date(time = pick(time.find("time")), 
                          day = pickn(time.find("day")), 
                          month = pickn(time.find("month")), 
                          year = pickn(time.find("year")), 
                          misc = pick(time.find("misc")))
        time_model.put()
        info_model.time = time_model.key()
        
        loc = info.find("loc")
        loc_model = Location(city = pick(loc.find("city")), 
                             region = pick(loc.find("region")), 
                             country = pick(loc.find("country")))
        loc_model.put()
        
        info_model.loc = loc_model.key()
        impact = info.find("impact")
        
        human = impact.find("human")
        human_model = HumanImpact(deaths = pickn(human.find("deaths")), 
                                  displaced = pickn(human.find("displaced")), 
                                  injured = pickn(human.find("injured")), 
                                  missing = pickn(human.find("missing")), 
                                  misc = pick(human.find("misc")))
        human_model.put() #saves the model
        
        economic = impact.find("economic")
        economic_model = EconomicImpact(amount = pickn(human.find("amount")), 
                                        currency = pick(human.find("currency")), 
                                        misc = pick(human.find("misc")))
        economic_model.put()
        impact_model = Impact(human = human_model.key(), economic = economic_model.key())
        impact_model.put()
        
        info_model.impact = impact_model.key()
        info_model.put()
        crisis_model.info = info_model.key()
        
        ref = crisis.find("ref")
        primaryImage = ref.find("primaryImage")
        ref_model = Reference()
        pimage_model = Link(site = pick(primaryImage.find("site")), 
                            title = pick(primaryImage.find("title")), 
                            url = pick(primaryImage.find("url")), 
                            description = pick(primaryImage.find("description")))
        pimage_model.put()
        ref_model.primaryImage = pimage_model.key()
        images = ref.findall("image")
        for image in images:
            link_model = Link(site = pick(image.find("site")), 
                              title = pick(image.find("title")), 
                              url = pick(image.find("url")), 
                              description = pick(image.find("description")))
            link_model.put()
            ref_model.images.append(link_model.key())
        videos = ref.findall("video")
        for video in videos:
            link_model = Link(site = pick(video.find("site")), 
                              title = pick(video.find("title")), 
                              url = pick(video.find("url")), 
                              description = pick(video.find("description")))
            link_model.put()
            ref_model.videos.append(link_model.key())
        socials = ref.findall("social") 
        for social in socials:
            link_model = Link(site = pick(social.find("site")), 
                              title = pick(social.find("title")), 
                              url = pick(social.find("url")), 
                              description = pick(social.find("description")))
            link_model.put()
            ref_model.socials.append(link_model.key())
        exts = ref.findall("ext")
        for ext in exts:
            link_model = Link(site = pick(ext.find("site")), 
                              title = pick(ext.find("title")), 
                              url = pick(ext.find("url")), 
                              description = pick(ext.find("description")))
            link_model.put()
            ref_model.exts.append(link_model.key())
        ref_model.put()
        crisis_model.ref = ref_model.key()
        
        crisis_model.misc = pick(crisis.find("misc"))
        #debug(crisis_model.misc)
        """
        #the keys don't exist at this point
        relatedOrgs = crisis.findall("org")
        for relatedOrg in relatedOrgs:
            crisis_model.relatedOrgs.append(Organization.get_by_key_name(relatedOrg.attrib["idref"]).key())
        relatedPeople = crisis.findall("person")
        for relatedPerson in relatedPeople:
            crisis_model.relatedPeople.append(Person.get_by_key_name(relatedPerson.attrib["idref"]).key())
        """
        
        crisis_model.put()
        data.append(crisis_model)
    
    orgs = root.findall("organization")
    for org in orgs: 
        org_model = Organization(key_name = org.attrib["id"], idref = org.attrib["id"], name = org.find("name").text)
        
        info = org.find("info")
        info_model = OrgInfo(type_ = pick(info.find("type")), 
                             history = pick(info.find("history")))
        contact = info.find("contact")
        contact_model = ContactInfo(phone = pick(contact.find("phone")), 
                                    email = pick(contact.find("email")))
        mail = contact.find("mail")
        mail_model = FullAddress(addr = pick(mail.find("address")), 
                                 city = pick(mail.find("city")), 
                                 state = pick(mail.find("state")), 
                                 country = pick(mail.find("country")), 
                                 zip_ = pick(mail.find("zip")))
        mail_model.put()
        contact_model.mail = mail_model.key()
        contact_model.put()
        info_model.contact = contact_model
        
        loc = info.find("loc")
        loc_model = Location(city = pick(loc.find("city")), 
                             region = pick(loc.find("region")), 
                             country = pick(loc.find("country")))
        loc_model.put()
        info_model.loc = loc_model.key()
        info_model.put()
        org_model.info = info_model.key()
        
        ref = org.find("ref")
        primaryImage = ref.find("primaryImage")
        ref_model = Reference()
        pimage_model = Link(site = pick(primaryImage.find("site")), 
                            title = pick(primaryImage.find("title")), 
                            url = pick(primaryImage.find("url")), 
                            description = pick(primaryImage.find("description")))
        pimage_model.put()
        ref_model.primaryImage = pimage_model.key()
        images = ref.findall("image")
        for image in images:
            link_model = Link(site = pick(image.find("site")), 
                              title = pick(image.find("title")), 
                              url = pick(image.find("url")), 
                              description = pick(image.find("description")))
            link_model.put()
            ref_model.images.append(link_model.key())
        videos = ref.findall("video")
        for video in videos:
            link_model = Link(site = pick(video.find("site")), 
                              title = pick(video.find("title")), 
                              url = pick(video.find("url")), 
                              description = pick(video.find("description")))
            link_model.put()
            ref_model.videos.append(link_model.key())
        socials = ref.findall("social") 
        for social in socials:
            link_model = Link(site = pick(social.find("site")), 
                              title = pick(social.find("title")), 
                              url = pick(social.find("url")), 
                              description = pick(social.find("description")))
            link_model.put()
            ref_model.socials.append(link_model.key())
        exts = ref.findall("ext")
        for ext in exts:
            link_model = Link(site = pick(ext.find("site")), 
                              title = pick(ext.find("title")), 
                              url = pick(ext.find("url")), 
                              description = pick(ext.find("description")))
            link_model.put()
            ref_model.exts.append(link_model.key())
        ref_model.put()
        org_model.ref = ref_model.key()
        
        org_model.misc = pick(org.find("misc"))
        """
        relatedCrises = org.findall("crisis")
        for relatedCrisis in relatedCrises:
            org_model.relatedCrises.append(Crisis.get_by_key_name(relatedCrisis.attrib["idref"]).key())
        relatedPeople = org.findall("person")
        for relatedPerson in relatedPeople:
            org_model.relatedPeople.append(Person.get_by_key_name(relatedPerson.attrib["idref"]).key())
        """
        
        org_model.put()
        data.append(org_model)
        
    people = root.findall("person")
    for person in people: 
        person_model = Person(key_name = person.attrib["id"], idref = person.attrib["id"], name = person.find("name").text)
        info = person.find("info")
        
        info = person.find("info")
        info_model = PersonInfo(type_ = pick(info.find("type")), 
                                nationality = pick(info.find("nationality")), 
                                biography = pick(info.find("biography")))
        
        birthdate = info.find("birthdate")
        birthdate_model = Date(time = pick(birthdate.find("time")), 
                               day = pickn(birthdate.find("day")), 
                               month = pickn(birthdate.find("month")), 
                               year = pickn(birthdate.find("year")), 
                               misc = pick(birthdate.find("misc")))
        birthdate_model.put()
        info_model.birthdate = birthdate_model
        
        info_model.put()
        person_model.info = info_model.key()
        
        ref = person.find("ref")
        primaryImage = ref.find("primaryImage")
        ref_model = Reference()
        pimage_model = Link(site = pick(primaryImage.find("site")), 
                            title = pick(primaryImage.find("title")), 
                            url = pick(primaryImage.find("url")), 
                            description = pick(primaryImage.find("description")))
        pimage_model.put()
        ref_model.primaryImage = pimage_model.key()
        images = ref.findall("image")
        for image in images:
            link_model = Link(site = pick(image.find("site")), 
                              title = pick(image.find("title")), 
                              url = pick(image.find("url")), 
                              description = pick(image.find("description")))
            link_model.put()
            ref_model.images.append(link_model.key())
        videos = ref.findall("video")
        for video in videos:
            link_model = Link(site = pick(video.find("site")), 
                              title = pick(video.find("title")), 
                              url = pick(video.find("url")), 
                              description = pick(video.find("description")))
            link_model.put()
            ref_model.videos.append(link_model.key())
        socials = ref.findall("social") 
        for social in socials:
            link_model = Link(site = pick(social.find("site")), 
                              title = pick(social.find("title")), 
                              url = pick(social.find("url")), 
                              description = pick(social.find("description")))
            link_model.put()
            ref_model.socials.append(link_model.key())
        exts = ref.findall("ext")
        for ext in exts:
            link_model = Link(site = pick(ext.find("site")), 
                              title = pick(ext.find("title")), 
                              url = pick(ext.find("url")), 
                              description = pick(ext.find("description")))
            link_model.put()
            ref_model.exts.append(link_model.key())
        ref_model.put()
        person_model.ref = ref_model.key()        
        
        person_model.misc = pick(person.find("misc"))
        """
        relatedCrises = person.findall("crisis")
        for relatedCrisis in relatedCrises:
            person_model.relatedCrises.append(Crisis.get_by_key_name(relatedCrisis.attrib["idref"]).key())
        relatedOrgs = person.findall("org")
        for relatedOrg in relatedOrgs:
            person_model.relatedOrgs.append(Organization.get_by_key_name(relatedOrg.attrib["idref"]).key())
        """
        
        person_model.put()
        data.append(person_model)
    """
    for crisis in crises:
        relatedOrgs = crisis.findall("org")
        for relatedOrg in relatedOrgs:
            
            
            #debug("A. " + Crisis.get_by_key_name(crisis.attrib["id"]).name)
            #debug("B. " + Crisis.get_by_key_name(crisis.attrib["id"]).misc)
            
            Crisis.get_by_key_name(crisis.attrib["id"]).relatedOrgs.append(Organization.get_by_key_name(relatedOrg.attrib["idref"]).key())
            
        relatedPeople = crisis.findall("person")
        for relatedPerson in relatedPeople:
            Crisis.get_by_key_name(crisis.attrib["id"]).relatedPeople.append(Person.get_by_key_name(relatedPerson.attrib["idref"]).key())
    for org in orgs:
        relatedCrises = org.findall("crisis")
        for relatedCrisis in relatedCrises:
            Organization.get_by_key_name(org.attrib["id"]).relatedCrises.append(Crisis.get_by_key_name(relatedCrisis.attrib["idref"]).key())
        relatedPeople = org.findall("person")
        for relatedPerson in relatedPeople:
            Organization.get_by_key_name(org.attrib["id"]).relatedPeople.append(Person.get_by_key_name(relatedPerson.attrib["idref"]).key())
    for person in people:
        relatedCrises = person.findall("crisis")
        for relatedCrisis in relatedCrises:
            Person.get_by_key_name(person.attrib["id"]).relatedCrises.append(Crisis.get_by_key_name(relatedCrisis.attrib["idref"]).key())
        relatedOrgs = person.findall("org")
        for relatedOrg in relatedOrgs:
            Person.get_by_key_name(person.attrib["id"]).relatedOrgs.append(Organization.get_by_key_name(relatedOrg.attrib["idref"]).key())
    """
    return data

# ------
# fixAmp
# ------
def fixAmp(line):
    """
    Replaces every occurrence of an ampersand(&) with "&amp;" in a given string
    line the original string
    return the modified string
    """
    result = ""
    for c in line:
        if c == '&':
            result += "&amp;"
        else:
            result += c
    return result

# ---------
# ExportXml
# ---------

def ExportXml(data):
    """
    Exports the data to the screen in xml format
    data is the data
    return a string in xml format
    """
    
    myString = ["<worldCrises>\n"]
    
    for crisis in data["crises"]:
        myString.append("\t<crisis id=\"" + data["crises"][crisis].idref + "\">\n")
        myString.append("\t\t<name>" + data["crises"][crisis].name + "</name>\n")
        myString.append("\t\t<info>\n")
        myString.append("\t\t\t<history>" + data["crises"][crisis].info.history + "</history>\n")
        myString.append("\t\t\t<help>" + data["crises"][crisis].info.help + "</help>\n")
        myString.append("\t\t\t<resources>" + data["crises"][crisis].info.resources + "</resources>\n")
        myString.append("\t\t\t<type>" + data["crises"][crisis].info.type_ + "</type>\n")
        myString.append("\t\t\t<history>" + data["crises"][crisis].info.history + "</history>\n")
        myString.append("\t\t\t<time>\n")
        myString.append("\t\t\t\t<time>" + data["crises"][crisis].info.time.time + "</time>\n")
        myString.append("\t\t\t\t<day>" + data["crises"][crisis].info.time.day + "</day>\n")
        myString.append("\t\t\t\t<month>" + data["crises"][crisis].info.time.month + "</month>\n")
        myString.append("\t\t\t\t<year>" + data["crises"][crisis].info.time.year + "</year>\n")
        myString.append("\t\t\t\t<misc>" + data["crises"][crisis].info.time.misc + "</misc>\n")
        myString.append("\t\t\t</time>\n")
        myString.append("\t\t\t<loc>\n")
        myString.append("\t\t\t\t<city>" + data["crises"][crisis].info.loc.city + "</city>\n")
        myString.append("\t\t\t\t<region>" + data["crises"][crisis].info.loc.region + "</region>\n")
        myString.append("\t\t\t\t<country>" + data["crises"][crisis].info.loc.country + "</country>\n")
        myString.append("\t\t\t</loc>\n")
        myString.append("\t\t\t<impact>\n")
        myString.append("\t\t\t\t<human>\n")
        myString.append("\t\t\t\t\t<deaths>" + data["crises"][crisis].info.impact.human.deaths + "</deaths>\n")
        myString.append("\t\t\t\t\t<displaced>" + data["crises"][crisis].info.impact.human.displaced + "</displaced>\n")
        myString.append("\t\t\t\t\t<injured>" + data["crises"][crisis].info.impact.human.injured + "</injured>\n")
        myString.append("\t\t\t\t\t<missing>" + data["crises"][crisis].info.impact.human.missing + "</missing>\n")
        myString.append("\t\t\t\t\t<misc>" + data["crises"][crisis].info.impact.human.misc + "</misc>\n")
        myString.append("\t\t\t\t</human>\n")
        myString.append("\t\t\t\t<economic>\n")
        myString.append("\t\t\t\t\t<amount>" + data["crises"][crisis].info.impact.economic.amount + "</amount>\n")
        myString.append("\t\t\t\t\t<currency>" + data["crises"][crisis].info.impact.economic.currency + "</currency>\n")
        myString.append("\t\t\t\t\t<misc>" + data["crises"][crisis].info.impact.economic.misc + "</misc>\n")
        myString.append("\t\t\t\t</economic>\n")
        myString.append("\t\t\t</impact>\n")
        myString.append("\t\t</info>\n")
        myString.append("\t\t<ref>\n")
        myString.append("\t\t\t<primaryImage>\n")
        myString.append("\t\t\t\t<site>" + data["crises"][crisis].ref.primaryImage.site + "</site>\n")
        myString.append("\t\t\t\t<title>" + data["crises"][crisis].ref.primaryImage.title + "</title>\n")
        myString.append("\t\t\t\t<url>" + data["crises"][crisis].ref.primaryImage.url + "</url>\n")
        myString.append("\t\t\t\t<description>" + data["crises"][crisis].ref.primaryImage.description + "</description>\n")
        myString.append("\t\t\t</primaryImage>\n")
        for image in data["crises"][crisis].ref.images:
        	myString.append("\t\t\t<image>\n")
        	myString.append("\t\t\t\t<site>" + data["crises"][crisis].ref.image.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["crises"][crisis].ref.image.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["crises"][crisis].ref.image.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["crises"][crisis].ref.image.description + "</description>\n")
        	myString.append("\t\t\t</image>\n")
        for video in data["crises"][crisis].ref.videos:
        	myString.append("\t\t\t<video>\n")
        	myString.append("\t\t\t\t<site>" + data["crises"][crisis].ref.video.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["crises"][crisis].ref.video.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["crises"][crisis].ref.video.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["crises"][crisis].ref.video.description + "</description>\n")
        	myString.append("\t\t\t</video>\n")
        for social in data["crises"][crisis].ref.socials:
        	myString.append("\t\t\t<social>\n")
        	myString.append("\t\t\t\t<site>" + data["crises"][crisis].ref.social.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["crises"][crisis].ref.social.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["crises"][crisis].ref.social.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["crises"][crisis].ref.social.description + "</description>\n")
        	myString.append("\t\t\t</social>\n")
        for ext in data["crises"][crisis].ref.exts:
        	myString.append("\t\t\t<ext>\n")
        	myString.append("\t\t\t\t<site>" + data["crises"][crisis].ref.ext.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["crises"][crisis].ref.ext.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["crises"][crisis].ref.ext.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["crises"][crisis].ref.ext.description + "</description>\n")
        	myString.append("\t\t\t</ext>\n")
        myString.append("\t\t</ref>\n")
        myString.append("\t\t<misc>" + data["crises"][crisis].misc + "</misc>\n")
        for org in data["crises"][crisis].relatedOrgs: 
        	myString.append("<org idref=\"" + org.idref + "\"></org>")
        for person in data["crises"][crisis].relatedPeople:
        	myString.append("<person idref=\"" + person.idref + "\"></org>")
        myString.append("\t<\crisis>\n")
        
    for org in data["orgs"]:
        myString.append("\t<organization id=\""+data["orgs"][org].idref+"\">\n")
        myString.append("\t\t<name>" + data["orgs"][org].name + "</name>\n")
        myString.append("\t\t<info>\n")
        myString.append("\t\t\t<type>" + data["orgs"][org].info.type_ + "</type>\n")
        myString.append("\t\t\t<history>" + data["orgs"][org].info.history + "</history>\n")
        myString.append("\t\t\t<contact>\n")
        myString.append("\t\t\t\t<phone>" + data["orgs"][org].info.contact.phone + "</phone>\n")
        myString.append("\t\t\t\t<email>" + data["orgs"][org].info.contact.email + "</email>\n")
        myString.append("\t\t\t\t<mail>\n")
        myString.append("\t\t\t\t\t<address>" + data["orgs"][org].info.contact.mail.address + "</address>\n")
        myString.append("\t\t\t\t\t<city>" + data["orgs"][org].info.contact.mail.city + "</city>\n")
        myString.append("\t\t\t\t\t<state>" + data["orgs"][org].info.contact.mail.state + "</state>\n")
        myString.append("\t\t\t\t\t<country>" + data["orgs"][org].info.contact.mail.country + "</country>\n")
        myString.append("\t\t\t\t\t<zip>" + data["orgs"][org].info.contact.mail.zip + "</zip>\n")
        myString.append("\t\t\t\t</mail>\n")
        myString.append("\t\t\t</contact>\n")
        myString.append("\t\t\t<loc>\n")
        myString.append("\t\t\t\t<city>" + data["orgs"][org].info.loc.city + "</city>\n")
        myString.append("\t\t\t\t<region>" + data["orgs"][org].info.loc.region + "</region>\n")
        myString.append("\t\t\t\t<country>" + data["orgs"][org].info.loc.country + "</country>\n")
        myString.append("\t\t\t</loc>\n")
        myString.append("\t\t</info>\n")
        myString.append("\t\t<ref>\n")
        myString.append("\t\t\t<primaryImage>\n")
        myString.append("\t\t\t\t<site>" + data["orgs"][org].ref.primaryImage.site + "</site>\n")
        myString.append("\t\t\t\t<title>" + data["orgs"][org].ref.primaryImage.title + "</title>\n")
        myString.append("\t\t\t\t<url>" + data["orgs"][org].ref.primaryImage.url + "</url>\n")
        myString.append("\t\t\t\t<description>" + data["orgs"][org].ref.primaryImage.description + "</description>\n")
        myString.append("\t\t\t</primaryImage>\n")
        for image in data["orgs"][org].ref.images:
        	myString.append("\t\t\t<image>\n")
        	myString.append("\t\t\t\t<site>" + data["orgs"][org].ref.image.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["orgs"][org].ref.image.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["orgs"][org].ref.image.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["orgs"][org].ref.image.description + "</description>\n")
        	myString.append("\t\t\t</image>\n")
        for video in data["orgs"][org].ref.videos:
        	myString.append("\t\t\t<video>\n")
        	myString.append("\t\t\t\t<site>" + data["orgs"][org].ref.video.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["orgs"][org].ref.video.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["orgs"][org].ref.video.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["orgs"][org].ref.video.description + "</description>\n")
        	myString.append("\t\t\t</video>\n")
        for social in data["orgs"][org].ref.socials:
        	myString.append("\t\t\t<social>\n")
        	myString.append("\t\t\t\t<site>" + data["orgs"][org].ref.social.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["orgs"][org].ref.social.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["orgs"][org].ref.social.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["orgs"][org].ref.social.description + "</description>\n")
        	myString.append("\t\t\t</social>\n")
        for ext in data["orgs"][org].ref.exts:
        	myString.append("\t\t\t<ext>\n")
        	myString.append("\t\t\t\t<site>" + data["orgs"][org].ref.ext.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["orgs"][org].ref.ext.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["orgs"][org].ref.ext.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["orgs"][org].ref.ext.description + "</description>\n")
        	myString.append("\t\t\t</ext>\n")
        myString.append("\t\t</ref>\n")
        myString.append("\t\t<misc>" + data["orgs"][org].misc + "</misc>\n")
        for crisis in data["orgs"][org].relatedCrises: 
        	myString.append("<crisis idref=\"" + crisis.idref + "\"></org>")
        for person in data["orgs"][org].relatedPeople:
        	myString.append("<person idref=\"" + person.idref + "\"></org>")
        myString.append("\t<\organization>\n")
        
    for person in data["people"]:
        myString.append("\t<person id=\""+data["people"][person].idref+"\">\n")
        myString.append("\t\t<name>" + data["people"][person].name + "</name>\n")
        myString.append("\t\t<info>\n")
        myString.append("\t\t\t<type>" + data["people"][person].info.type_ + "</type>\n")
        myString.append("\t\t\t<birthdate>\n")
        myString.append("\t\t\t\t<time>" + data["people"][person].info.birthdate.time + "</time>\n")
        myString.append("\t\t\t\t<day>" + data["people"][person].info.birthdate.day + "</day>\n")
        myString.append("\t\t\t\t<year>" + data["people"][person].info.birthdate.year + "</year>\n")
        myString.append("\t\t\t\t<misc>" + data["people"][person].info.birthdate.misc + "</misc>\n")
        myString.append("\t\t\t</birthdate>\n")
        myString.append("\t\t\t<nationality>" + data["people"][person].info.nationality + "</nationality>\n")
        myString.append("\t\t\t<biography>" + data["people"][person].info.biography + "</biography>\n")
        myString.append("\t\t</info>\n")
        myString.append("\t\t<ref>\n")
        myString.append("\t\t\t<primaryImage>\n")
        myString.append("\t\t\t\t<site>" + data["people"][person].ref.primaryImage.site + "</site>\n")
        myString.append("\t\t\t\t<title>" + data["people"][person].ref.primaryImage.title + "</title>\n")
        myString.append("\t\t\t\t<url>" + data["people"][person].ref.primaryImage.url + "</url>\n")
        myString.append("\t\t\t\t<description>" + data["people"][person].ref.primaryImage.description + "</description>\n")
        myString.append("\t\t\t</primaryImage>\n")
        for image in data["people"][person].ref.images:
        	myString.append("\t\t\t<image>\n")
        	myString.append("\t\t\t\t<site>" + data["people"][person].ref.image.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["people"][person].ref.image.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["people"][person].ref.image.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["people"][person].ref.image.description + "</description>\n")
        	myString.append("\t\t\t</image>\n")
        for video in data["people"][person].ref.videos:
        	myString.append("\t\t\t<video>\n")
        	myString.append("\t\t\t\t<site>" + data["people"][person].ref.video.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["people"][person].ref.video.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["people"][person].ref.video.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["people"][person].ref.video.description + "</description>\n")
        	myString.append("\t\t\t</video>\n")
        for social in data["people"][person].ref.socials:
        	myString.append("\t\t\t<social>\n")
        	myString.append("\t\t\t\t<site>" + data["people"][person].ref.social.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["people"][person].ref.social.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["people"][person].ref.social.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["people"][person].ref.social.description + "</description>\n")
        	myString.append("\t\t\t</social>\n")
        for ext in data["people"][person].ref.exts:
        	myString.append("\t\t\t<ext>\n")
        	myString.append("\t\t\t\t<site>" + data["people"][person].ref.ext.site + "</site>\n")
        	myString.append("\t\t\t\t<title>" + data["people"][person].ref.ext.title + "</title>\n")
        	myString.append("\t\t\t\t<url>" + data["people"][person].ref.ext.url + "</url>\n")
        	myString.append("\t\t\t\t<description>" + data["people"][person].ref.ext.description + "</description>\n")
        	myString.append("\t\t\t</ext>\n")
        myString.append("\t\t</ref>\n")
        myString.append("\t\t<misc>" + data["people"][person].misc + "</misc>\n")
        for crisis in data["people"][person].relatedCrises: 
        	myString.append("<crisis idref=\"" + crisis.idref + "\"></org>")
        for org in data["people"][person].relatedOrgs: 
        	myString.append("<org idref=\"" + org.idref + "\"></org>")
        myString.append("\t<\person>\n")
        
    myString.append("</worldCrises>")
    return "".join(myString)

# -----
# Debug
# -----

def debug(msg):
    """
    prints the debug message
    msg the string you want to put on the debug screen
    """
    logging.debug("\n\n" + str(msg) + "\n")

def main():
    application = webapp.WSGIApplication([  ('/', MainHandler), 
                                            ('/import', ImportFormHandler), 
                                            ('/import_upload', ImportUploadHandler),
                                            ('/export', ExportHandler),
                                            ('/.*', MainHandler)
                                         ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

