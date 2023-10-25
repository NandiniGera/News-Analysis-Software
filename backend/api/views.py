from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
import requests
from bs4 import BeautifulSoup
import threading
import time
import xlsxwriter
import pandas as pd
import contractions
import re
import nltk
from nltk.tokenize import ToktokTokenizer
import spacy
import nltk
import pandas as pd
import ssl
from keras.models import load_model
from transformers import TFDistilBertModel
ssl._create_default_https_context = ssl._create_unverified_context
from transformers import DistilBertTokenizer




custom_objects = {'TFDistilBertModel': TFDistilBertModel}

loaded_model = load_model("distilbert_model.h5", custom_objects=custom_objects)
categories = {
0:"Entertainment",
1:"Business" ,
2:"Politics" ,
3:"Judiciary" ,
4:"Crime"  ,
5:"Culture" ,
6:"Sports" ,
7:"Science"  ,
8:"International" ,
9:"Technology" 
}
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
print("tokenizer ready")
max_length = 512

def predict_text(loaded_model, text):

    inputs = tokenizer(text, return_tensors='tf', truncation=True, padding='max_length', max_length=max_length)
    

    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']
    

    predictions = loaded_model.predict([input_ids, attention_mask])
    
    return predictions

def classification(row):


    example_text = row
    predictions = predict_text(loaded_model, example_text)

    value_to_find = predictions[0].argmax()
    predicted_class = categories[value_to_find]
    return predicted_class

def preprocess(series):
    series = series.apply(lambda x: str(x).lower())
    
    def remove_contractions(row):
        return contractions.fix(row)
    series = series.apply(lambda x: remove_contractions(x))
    
    series = series.str.replace(r'[^\w\s]', '', regex=True)
    
    series = series.str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
    
    def remove_numbers(text):
        pattern = r'[^a-zA-z.,!?/:;\"\'\s]' 
        return re.sub(pattern, '', text)
    series = series.apply(lambda x: remove_numbers(x))
    
    nlp = spacy.load('en_core_web_sm')
    def get_lem(text):
        text = nlp(text)
        text = ' '.join([word.lemma_ if word.lemma_ != '-PRON-' else word.text for word in text])
        return text
    series = series.apply(lambda x: get_lem(x))
    
    tokenizer = ToktokTokenizer()
    stopword_list = nltk.corpus.stopwords.words('english')
    stopword_list.remove('not')
    def remove_stopwords(text):
        tokens = tokenizer.tokenize(text)
        tokens = [token.strip() for token in tokens]
        t = [token for token in tokens if token.lower() not in stopword_list]
        text = ' '.join(t)    
        return text
    series = series.apply(lambda x: remove_stopwords(x))
    return series


def PreProcessTheData():
    df = pd.read_excel("IndiaToday.xlsx")
    def remove_edited(row):
        index_of_edited_by = row.find("Edited By: ")

        if index_of_edited_by != -1:
            modified_text = row[:index_of_edited_by]
            return modified_text
        else:
            return row
    df.Body = df.Body.apply(lambda x: remove_edited(x)) 
    df = df[~df['Body'].apply(lambda x: isinstance(x, (float, int)))]
    df = df[~df['Heading'].str.contains('horoscope', case=False)]
    df.Body = preprocess(df.Body)
    df = df.dropna()
    df2 = pd.read_excel("IndiaTv.xlsx")
    df2 = df2[~df2['Body'].apply(lambda x: isinstance(x, (float, int)))]
    df2 = df2[~(df2['Body'].str.contains('dear subscriber', case=False))]
    df2 = df2[~df2['Heading'].str.contains('horoscope', case=False)]
    df2.Body = preprocess(df2.Body)
    df2 = df2.dropna()
    df3 = pd.concat([df,df2], ignore_index=True, axis=0, join='outer')
    df3["Cat"]=df3["Body"].apply(lambda x:classification(str(x)))
    df3.shape
    file_name = "Final_Prepped_Data.xlsx"
    df3.to_excel(file_name, index=False)
    
    

       
def IndiaTv():
    workbook=xlsxwriter.Workbook('IndiaTv.xlsx')
    worksheet=workbook.add_worksheet()
    row=0
    column=0
    worksheet.write(row,column,"Heading")
    worksheet.write(row,column+1,"Body")
    worksheet.write(row,column+2,"Category")
    worksheet.write(row,column+3,"URL")
    row+=1
    HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
    r=requests.get('https://www.indiatvnews.com', headers=HEADERS)
    urls_to_visit=[]
    unique_urls={}
    count=0
    try:
        if(r.status_code==200):
            soup=BeautifulSoup(r.text, 'html.parser')
            for url in soup.findAll('a'):
                try:
                    if(url.has_attr('href')):
                        if("video" not in url['href'].split("/") and "tag" not in url['href'].split("/") and "author" not in url['href'].split("/")):
                            if(url['href'][0]=='/' and "https://www.indiatvnews.com"+url['href'] not in unique_urls.keys()):
                                unique_urls["https://www.indiatvnews.com"+url['href']]=True
                                urls_to_visit.append("https://www.indiatvnews.com"+url['href'])
                            elif(url['href'][0]=='h' and url['href'].split("/")[2]=="www.indiatvnews.com" and url['href'] not in unique_urls.keys()):
                                unique_urls[url['href']]=True
                                urls_to_visit.append(url['href'])
                finally:
                    continue
        while(urls_to_visit and count<20):
                urltoVisit=urls_to_visit[0]
                
                urls_to_visit.pop(0)
                if(urltoVisit[0]=='h' and (["tags","tag", "livetv?utm_source=mobiletophead&amp;utm_campaign=livetvlink", "video", "news-podcasts", "lifestyle","astrology", "web-stories"] not in urltoVisit.split("/"))):
                    try:
                        r=requests.get(urltoVisit, headers=HEADERS)
                        if(r.status_code==200):
                            soup=BeautifulSoup(r.text, 'html.parser')
                            for url in soup.findAll('a'):
                                try:
                                    if(url.has_attr('href')):
                                        if("video" not in url['href'].split("/") and "tag" not in url['href'].split("/") and "author" not in url['href'].split("/")):
                                            if(url['href'][0]=='/' and "https://www.indiatvnews.com"+url['href'] not in unique_urls.keys()):
                                                unique_urls["https://www.indiatvnews.com"+url['href']]=True
                                                urls_to_visit.append("https://www.indiatvnews.com"+url['href'])
                                            elif(url['href'][0]=='h' and url['href'].split("/")[2]=="www.indiatvnews.com" and url['href'] not in unique_urls.keys()):
                                                unique_urls[url['href']]=True
                                                urls_to_visit.append(url['href'])
                                finally:
                                    continue
                            
                            if(soup.find('div', {'class':'article-title'}) and (soup.find('html',{'lang':'en'}) or soup.find('html',{'lang':'en-us'})or soup.find('html',{'lang':'en-uk'})) ):
                                heading_title=soup.find('div', {'class':'article-title'}).find('h1')
                                
                                if(soup.find('div', {'id':'content'}).findAll('p')):
                               
                                    heading_desc=soup.find('div', {'id':'content'}).findAll('p')
                                    news=""
                                    for i in range(len(heading_desc)-4):
                                       
                                        news+=heading_desc[i].text
                                    worksheet.write(row,column,heading_title.text)
                                    worksheet.write(row,column+1,news)
                                    if(urltoVisit.split("/")[3]!='news'):
                                        worksheet.write(row,column+2,urltoVisit.split("/")[4])
                                    else:
                                        worksheet.write(row,column+2,urltoVisit.split("/")[3])
                                    worksheet.write(row,column+3,urltoVisit)
                              
                                    row+=1
                                    
                                    count+=1
                    finally:
                        continue        
            
        
    finally:
        print("IndiaTv finished")
        workbook.close()
        IndiaToday()




def IndiaToday():
    workbook=xlsxwriter.Workbook('IndiaToday.xlsx')
    worksheet=workbook.add_worksheet()
    row=0
    column=0
    worksheet.write(row,column,"Heading")
    worksheet.write(row,column+1,"Body")
    worksheet.write(row,column+2,"Category")
    worksheet.write(row,column+3,"URL")
    row+=1
    HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
    r=requests.get('https://www.indiatoday.in', headers=HEADERS)
    urls_to_visit=[]
    unique_urls={}
    count=0
    try:
        if(r.status_code==200):
            soup=BeautifulSoup(r.text, 'html.parser')
            for url in soup.findAll('a'):
                try:
                    if(url.has_attr('href')):
                        if("video" not in url['href'].split("/") and "tag" not in url['href'].split("/") and "author" not in url['href'].split("/")):
                            if(url['href'][0]=='/' and "https://www.indiatoday.in"+url['href'] not in unique_urls.keys()):
                                unique_urls["https://www.indiatoday.in"+url['href']]=True
                                urls_to_visit.append("https://www.indiatoday.in"+url['href'])
                            elif(url['href'][0]=='h' and url['href'].split("/")[2]=="www.indiatoday.in" and url['href'] not in unique_urls.keys()):
                                unique_urls[url['href']]=True
                                urls_to_visit.append(url['href'])
                finally:
                    continue
        while(urls_to_visit and count<20):
                urltoVisit=urls_to_visit[0]
                urls_to_visit.pop(0)
           
                if(urltoVisit[0]=='h' and (["tags","tag", "livetv", "video"] not in urltoVisit.split("/"))):
                    try:
                        r=requests.get(urltoVisit, headers=HEADERS)
                        if(r.status_code==200):
                            soup=BeautifulSoup(r.text, 'html.parser')
                            for url in soup.findAll('a'):
                                try:
                                    if(url.has_attr('href')):
                                        if("video" not in url['href'].split("/") and "tag" not in url['href'].split("/") and "author" not in url['href'].split("/")):
                                            if(url['href'][0]=='/' and "https://www.indiatoday.in"+url['href'] not in unique_urls.keys()):
                                                unique_urls["https://www.indiatoday.in"+url['href']]=True
                                                urls_to_visit.append("https://www.indiatoday.in"+url['href'])
                                            elif(url['href'][0]=='h' and url['href'].split("/")[2]=="www.indiatoday.in" and url['href'] not in unique_urls.keys()):
                                                unique_urls[url['href']]=True
                                                urls_to_visit.append(url['href'])
                                finally:
                                    continue
                            
                            if(soup.find('div', {'class':'jsx-99cc083358cc2e2d Story_story__content__body__qCd5E story__content__body widgetgap'}) and (soup.find('html',{'lang':'en'}) or soup.find('html',{'lang':'en-us'})or soup.find('html',{'lang':'en-uk'}))):
                                heading_title=soup.find('div', {'class':'jsx-99cc083358cc2e2d Story_story__content__body__qCd5E story__content__body widgetgap'}).find('h1')
                                if(soup.find('div', {'class':'jsx-99cc083358cc2e2d Story_description__fq_4S description'}).findAll('p')):
                            
                                    
                                    
                                    heading_desc=soup.find('div', {'class':'jsx-99cc083358cc2e2d Story_description__fq_4S description'}).findAll('p')
                                    news=""
                                    for text in heading_desc:
                                        
                                        news+=text.text
                        
                                    worksheet.write(row,column,heading_title.text)
                                    worksheet.write(row,column+1,news)
                                    if(urltoVisit.split("/")[3]!='cities'):
                                        worksheet.write(row,column+2,urltoVisit.split("/")[3])
                                    else:
                                        worksheet.write(row,column+2,"india")
                                    worksheet.write(row,column+3,urltoVisit)
                              
                                    row+=1
                                    
                                    count+=1
                    finally:
                        continue        
            
        
    finally:
        print("India today finished")
        workbook.close()



  
def index (request):
    print("The Session started")
    # thread1 = threading.Thread(target=IndiaTv)
    # thread2 = threading.Thread(target=IndiaToday)

    # # Start the threads
    # thread1.start()
    # thread2.start()

    # # Wait for all threads to finish
    # thread1.join()
    # thread2.join()

    PreProcessTheData()
    news=[]
    df=pd.read_excel("Final_Prepped_Data.xlsx")
    for ind in df.index:
        row={}
        row["Title"]=df["Heading"][ind]
        row["Description"]=df["Body"][ind]
        row["URL"]=df["URL"][ind]
        row["Categories"]=df["Cat"][ind]
        news.append(row)
        
    print("PreProcessing Done")
    print("Session Ended")
    

    return JsonResponse({"result":"success", "News":news}, safe=False, json_dumps_params={'ensure_ascii': False})