from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import unquote,quote
from math import ceil
import random
import smtplib, ssl
from email.message import EmailMessage
import chromedriver_autoinstaller
from config import *

"""
Kryterium najważniejsze
1. Cena
2. Bezpłatne odwołanie
3. 2 sypialnie - obojętna kombinacja 1  duże lub 2 małe <- ręczenie 
4. Blisko plaży
5. Aneks kuchenny
6. Blisko sklep do 4km <-ręcznie!
Kryterium dodatkowe
7. Plaża - kamienista niż "skalna"
8. Ocena minimum 7.0
9. Liczba opini minimum 10 <- ręczenie
"""





class Booking_searching_offer():
    
    def __init__(self):
        #example full link:https://www.booking.com/searchresults.html?&checkin=2022-08-06&checkout=2022-08-13&dest_id=54&dest_type=country&group_adults=4&req_adults=4&no_rooms=2&group_children=0&req_children=0&nflt=class%3D3%3Bht_beach%3D1%3Bfc%3D2%3Bprice%3DPLN-min-400-1%3Breview_score%3D70%3Broomfacility%3D11%22&order=class&offset=0
        self.base_link = "https://www.booking.com/searchresults.html?"
        self.base_parameters = {
            'checkin':'2022-08-05',
            'checkout':'2022-08-12',
            'dest_id':'54',#chorwacja
            'dest_type':'country',
            'group_adults':'4',
            'req_adults':'4',
            'no_rooms':'2',
            'group_children':'0',
            'req_children':'0'
            
        }
        self.nflt_parameters = {
            'class':'3', #minimalna liczba gwiazdek
            'ht_beach':'1', #blisko plaży
            'fc': '2', #yyyyyyyy
            'price':'PLN-min-450-1',#minimalna i maksymalna kwota za nocleg
            'review_score':'70', #minimalna ocena 70->7 opinie przez klientów
            'roomfacility':'11' #klimatyzacja + aneks
            
        }
        self.full_link = ""
        chrome_options=Options()
        #chrome_options.add_argument("--lang=pl")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        #chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'pl,pl_PL'})
        self.browser = webdriver.Chrome(chromedriver_autoinstaller.install(),options=chrome_options)
        #self.browser = webdriver.Chrome('./chromedriver',options=chrome_options) #linux
        self.html_content_soup = ""
        self.filtres = ["2 sypialnie","2 łóżka podwójne"]
        self.good_offers = {
            
        }
        self.nazwy_ofert_zaladowanych_z_pliku = []
        self.page = 1

    def send_mail(self,message):

        port = 587  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = email_name_sender # Enter your address
        receiver_email = email_name_receiver1  # Enter receiver address
        password = password_for_sender
        em = EmailMessage()
        em.set_content(message)

        em['From'] = email_name_sender
        em['Subject'] = "Nowa oferta booking!"


        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, password)
            em['To'] = email_name_receiver1
            server.send_message(to_addrs=receiver_email,from_addr=sender_email,msg=em)

            em['To'] = email_name_receiver2
            server.send_message(to_addrs=email_name_receiver2,from_addr=sender_email,msg=em)

            em['To'] = email_name_receiver3
            server.send_message(to_addrs=email_name_receiver3,from_addr=sender_email,msg=em)

        sleep(1)


    def create_full_link(self):
        text1 = ""
        for key,value in self.base_parameters.items():
            text1 = text1 +f"&{key}={value}"

        text2 = ""
        
        #for nflt
        for key,value in self.nflt_parameters.items():
            text2 = text2 + f"{key}={value};"
        

        self.full_link = self.base_link+text1+"&nflt="+quote(text2[:-1])+quote('"')+'&order=class'

    def visit_website_first_time(self):
        self.visit_website_link(
            self.full_link
        )

    def next_page(self):
        new_link = self.full_link+"&offset="+str(self.page*25)
        self.visit_website_link(
            new_link
        )
        self.page = self.page + 1

        
    def visit_website_link(self,link):
        self.page = 1
        self.browser.get(link)
        html = self.browser.page_source
        self.html_content_soup = BeautifulSoup(html,'lxml')
        
    def check_the_number_of_offers(self):
        r = 0
        try:
            title = number_of_offers = self.html_content_soup.select(
                "h1.e1f827110f.d3a14d00da"
            )[0].text
            
            number_of_offers = title.split(" ")[2]
            
            r = int(number_of_offers)
        except Exception as e:
            r = 0
            print(
                f"error {e} Inna nazwa tytułu: {title}"
            )
        finally:
            print(r)
            return r
        
    def scrape_pages(self):
        fresh_offers = []
        number_of_offers = self.check_the_number_of_offers()
        if number_of_offers != -1:
            #print(int(ceil(number_of_offers/25)))
            ilosc_stron_do_zwiedzenia = int(ceil(number_of_offers/25))
            for i in range(0,ilosc_stron_do_zwiedzenia):
                
                oferty = self.html_content_soup.select(
                    'div[data-testid="property-card"]'
                )
                
                for oferta in oferty:
                    opisy = oferta.select('span.bb58e7a787') #wszystkie opisy dotyczące oferty
                    good_oferta = False
                    for opis in opisy:
                        if opis.text in self.filtres:
                            good_oferta = True
                            break
                    if good_oferta == True:
                        tytul = oferta.select('div[data-testid="title"]')[0].text
                        if tytul not in self.nazwy_ofert_zaladowanych_z_pliku:
                            link = oferta.select('a[data-testid="title-link"]')[0]['href']
                            fresh_offers.append(
                                [tytul,link]
                            )
                            self.good_offers[tytul] = link
                            print("Cyk nowa oferta")
                            
                            
                            
                if i!=ilosc_stron_do_zwiedzenia-1:
                    self.next_page()
        for tytul,link in fresh_offers:
            self.send_mail(
                                    f'Nazwa:{tytul} Link: {link}'
                                )        
                
    
    def show_offers(self):
        with open("wynik.txt","a+",encoding="utf-8") as f:
            for name,link in self.good_offers.items():
                if name not in self.nazwy_ofert_zaladowanych_z_pliku:
                    f.write(
                        f'Nazwa:{name} Link: {link}\n'
                    )
            print("Liczba ofert spełniająca warunek: ",len(self.good_offers))
                
    def read_offers(self):
        self.nazwy_ofert_zaladowanych_z_pliku = []
        try:
            with open("wynik.txt","r+",encoding="utf-8") as f:
                for line in f:
                    nazwa = line.split(" Link:")[0].split("Nazwa:")[1]
                    self.nazwy_ofert_zaladowanych_z_pliku.append(nazwa)
        except:
            print("Brak pliku do odczytu")
        # print(
        #     self.nazwy_ofert_zaladowanych_z_pliku
        # )
        
book = Booking_searching_offer()
book.create_full_link()
while True:      
    book.visit_website_first_time()
    book.read_offers()
    book.scrape_pages()
    book.show_offers()
    sleep(random.randint(60,300))





