import logging

logger = logging.getLogger(__name__)

class ChatService:

    def generate_response(self,message:str) -> str:

        logger.info("Generating chat response")

        return f"Meow! you said : {message}"