import logging

logger = logging.getLogger("yx-agent.mal")

class MailSender:

    def send(self,to: str, subject: str, body: str ) -> None:
        logger.info("[MAIL] to =%s subject=%s\n%s", to, subject, body)


mail_sender = MailSender()