import logging

logger = logging.getLogger(__name__)

class ChatService:

    def generate_response(self , message : str , session_id : str) -> str:

        logger.info("Generating chat response for session %s" , session_id)

        return f"Meow! you said : {message}"