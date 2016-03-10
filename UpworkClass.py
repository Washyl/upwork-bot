from selenium import webdriver
from selenium_automation import init_driver, goto, input_text, get_page_source,\
    click, get_driver, finds, request
from urlparse import urljoin
from lxml import html
import re
import time

class Upwork():
    username = ""
    password = ""
    proposal = """
    
    Hi,

    See the attachment of screen shot of a product built by us. It runs around 400 scrapers for one of our client.
    
    Get Technical help on your project or Idea free on Skype: dataspider99 
    
    We are expert in custom script writing. Previously We have done similar task for our clients on elance.com under the name "Tarlabs".
    
    In Job description you are not clear with technical requirements. Lets have a short chat with us.  
    
    !!! We may go for less price if needed !!!
    
    
    We are three and You can choose any of us(per Hour Price Variable).
    
    About Us:
    We are Expert in Scraping and scrape any website.(javaScript, Ajax, Logins etc.)
    Provide Support as well as do new developments.
    You can connect with us on skype: dataspider99
    
    Our Specialized fields : Django, Data Analytics, Data Mining, Web Scraping, Web Crawling ,Automation Testing, Automated Deployment(Docker) etc.
    
    With Regards,
    Manoj
    """
    
    def __init__(self,driver):
        init_driver(driver)    
        super(Upwork,self).__init__()
        
    def login(self):
        goto("https://www.upwork.com/Login")
        if not "Log in and get to work" in get_page_source():
            return
        input_text("#login_username",self.username)
        input_text("#login_password",self.password)
        #click("#login_rememberme")
        click("xpath=//button[contains(text(),'Log In')]")
        
    def find_work(self, keywords="Scrapy"):
        url = get_driver().current_url
        if url != "https://www.upwork.com/find-work-home/":
            goto("https://www.upwork.com/find-work-home/")
        if keywords:
            input_text("name=q", keywords)
            click("xpath=//input[@type='submit']")
            links_to_jobs = [urljoin(url,element.get_attribute("href")) for element in finds(".break")]
        else:
            links_to_jobs = [urljoin(url,element.get_attribute("href")) for element in finds(".oVisitedLink")]
        return self._job_details(links_to_jobs)
    
    def _clean(self,glue,List):
        return glue.join(List).strip()
        
    def _job_details(self, links):
        req = request()
        for link in links:
            job_detail = {}
            response = req.get(link)
            htmlObj = html.fromstring(response.text)
            job_detail['Heading'] = htmlObj.xpath("(//h1/text())[1]")
            job_detail['JobType'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[1]/div[1]/div[1]/div[2]/p/strong/text()")
            job_detail['Description'] = htmlObj.xpath("//p[@class='break']/text()")
            job_detail['Budget'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[1]/div[1]/div[2]/div/div[2]/p/strong/text()")    
            job_detail['HireRate'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[2]/p[4]/span/text()")
            job_detail['Feedback'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[2]/p[2]/strong/text()")
            job_detail['Url'] = [link]
            job_detail["_id"] = [link]
            job_detail['Amount'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[2]/p[5]/strong/text()")
            job_detail['HourlyRate'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[2]/p[6]/strong/text()")
            job_detail['PostDate'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[1]/small/span/@popover")
            job_detail['LastView'] = htmlObj.xpath("//span[contains(text(),'Last Viewed')]/parent::p/text()")
            job_detail['ProposalCount'] = htmlObj.xpath("//span[contains(@ng-bind,'applicantsCount')]/text()")
            job_detail['Interviewd'] = htmlObj.xpath("//span[contains(text(),'Interviewing')]/parent::p/text()")
            for key, value in job_detail.items():
                job_detail[key] = self._clean("", value)
            if 'hourly' in job_detail['JobType'].lower():
                job_detail['Experience'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[1]/div[1]/div[2]/div[2]/p/strong/text()")
            else:
                job_detail['Experience'] = htmlObj.xpath(".//*[@id='layout']/div[1]/div[3]/div[1]/div[1]/div[3]/div[2]/p/strong/text()")
            job_detail['Experience'] = self._clean("", job_detail['Experience'])
            if self.jobs.store_jobs(job_detail):
                yield job_detail
            else: 
                break
            
    def past_jobs(self, url="https://www.upwork.com/applications/archived/"):
        req = request()
        response = req.get(url)
        htmlObj = html.fromstring(response.text)
        links = htmlObj.xpath("//a[contains(@name,'job_')]/@href")
        self._job_details(links)
        next_page = htmlObj.xpath("//a[text()='Next']/@href")
        if next_page:
            return self.past_jobs(url = urljoin(response.url,next_page[0]))
        
    def apply_jobs(self,jobDetails, myRate=20, attachment_path = "/home/ubuntu/manoj/Pictures/Screenshot from 2016-01-11 19:10:06.png"):
        for jobDetail in jobDetails:
            goto(jobDetail['Url'])
            if "You have already applied to this job" in get_page_source():
                continue
            click("xpath=//section[@id='jobsProviderAction']/a")
            time.sleep(5)
            if "You do not meet all the client's preferred qualifications" in get_page_source():
                continue
            
            if jobDetail['JobType'] == 'Hourly Job':
                if jobDetail['HourlyRate']:
                    rate = re.sub("[^.\d]","",jobDetail['HourlyRate'])
                
                elif jobDetail['Experience'] == 'Entry Level':
                    rate = myRate/3
                elif jobDetail['Experience'] == 'Intermediate':
                    rate = myRate/2
                else:
                    rate = myRate
                    input_text("#employerRate",str(rate))
            else:
                price = int(re.sub("[^.\d]","",jobDetail['Budget']))
                price = price - (price/25)
                input_text("#employerRate", price)
                click("#duration")
                if price > 200:
                    click("xpath=//option[@value='4']")
                else:
                    click("xpath=//option[@value='5']")
            input_text("#coverLetter",self.proposal)
            input_text("#attachment", attachment_path)
            self.handle_additional_question()
            click("#submitButton")
            time.sleep(5)
            click("#applyFPHintCB")
            click(".jsApplyFPHintSubmit")
    
    def handle_additional_question(self):
        questions = finds("xpath=//textarea[contains(@id,'answers')]")
        for question in questions:
            input_text(question ,"We are working on this bot to answer you in future. FOr more info msg us or connect on skype: dataspider99") 

if __name__=="__main__":
    driver = webdriver.Chrome()
    upwork = Upwork(driver)
    upwork.login()
    jobs = upwork.find_work()
    upwork.apply_jobs(jobs)
    