import os
from glob import glob 
import pandas as pd
from pdf2image import convert_from_path
from datetime import datetime

class AnsPdf:
    def __init__(self):
        self.key = 'pdf_path'
        self.setup_log()
    
    def setup_log(self):
        self.log_path = '/home/ryh/embedding-match/ocr/datasets/ansPdf.pickle'
        self.log_columns = [self.key, 'created_time']
        try:
            self.log = pd.read_pickle(self.log_path)
        except:
            self.log = pd.DataFrame(columns=self.log_columns)
        self.path_set = set(self.log[self.key].values)
    
    def update_log(self, pdf_path):
        row = pd.DataFrame(columns=self.log_columns)
        
        row[self.key] = [pdf_path]
        row['created_time'] = [datetime.now()]
        
        self.log = self.log.append(row)
        self.path_set.add(pdf_path)
        
    def save_log(self):
        self.log = self.log.sort_values(by=self.key, ascending=True).reset_index(drop=True)
        self.log.to_pickle(self.log_path)
        
    def get_pdf_path_list(self, year='*', subject='*', press='*'):
        d = '/home/ryh/embedding-match/ocr/datasets/taiwan/13to15/press/%s/%s/%s/answer/pdf/*.pdf'%(year, subject, press)
        pdf_path_list = sorted(glob(d))
        return pdf_path_list
    
    def pdf2papers(self, pdf_path):
        if pdf_path in self.path_set: return
        
        images = convert_from_path(pdf_path)
        
        old_dirname = os.path.dirname(pdf_path)
        old_basename = os.path.basename(pdf_path)
        
        new_dirname = old_dirname.replace('pdf', 'prePaper')
        os.makedirs(new_dirname, exist_ok=True)
        for i, image in enumerate(images):     
            #print(i+1, len(images), end='\r')
            new_basename = old_basename.replace('.pdf', '') + '---%02d'%(i+1) + '.png' 
            img_path = os.path.join(new_dirname, new_basename)
            image.save(img_path, 'PNG')
            
        self.update_log(pdf_path)
        
    
ansPdf = AnsPdf()
pdf_path_list = ansPdf.get_pdf_path_list(year='108', subject='數學')

for i in range(len(pdf_path_list)):
    print(i+1, len(pdf_path_list), end='\r')
    pdf_path = pdf_path_list[i]
    ansPdf.pdf2papers(pdf_path)
ansPdf.save_log()
    