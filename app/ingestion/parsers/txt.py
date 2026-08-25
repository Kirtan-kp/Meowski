from app.ingestion.parsers.base import BaseParser

class TXTReader(BaseParser):

    def parse(self , file_path : str) -> str:

        with open(file_path , "r" , encoding = "utf-8") as file:
            
            return file.read()