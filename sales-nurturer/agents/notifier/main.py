import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Literal
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class Notifier:
    def __init__(self):
        self.logger = logging.getLogger("notifier")
        self.tracking_pixels = {}  # {pixel_id: metadata}
        self.router = APIRouter()
        self._setup_logging()
        self._setup_routes()

    def _setup_routes(self):
        """Initialize FastAPI routes"""
        @self.router.get("/track/{pixel_id}")
        async def track_open(pixel_id: str, request: Request):
            return self._handle_pixel(pixel_id)

        @self.router.get("/view/{email_id}")
        async def view_email(email_id: str):
            return self._handle_email_view(email_id)

    def _generate_pixel_url(self, email_id: str, lead_id: str) -> str:
        """Generate unique tracking pixel URL
        Args:
            email_id: Unique identifier for the email
            lead_id: Associated lead ID
        Returns:
            str: URL like 'https://yourdomain.com/track/abc123...'
        """
        pixel_id = str(uuid.uuid4())
        self.tracking_pixels[pixel_id] = {
            'email_id': email_id,
            'lead_id': lead_id,
            'timestamp': datetime.now().isoformat(),
            'ip': None,
            'user_agent': None
        }
        return f"https://yourdomain.com/track/{pixel_id}"  # Change to your domain

    def _handle_pixel(self, pixel_id: str) -> Response:
        """Serve tracking pixel and log open"""
        if pixel_id in self.tracking_pixels:
            metadata = self.tracking_pixels[pixel_id]
            
            # Log to your database (implement this)
            self._log_open_event(metadata)
            
            # Return 1x1 transparent GIF
            return Response(
                content=b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
                media_type="image/gif"
            )
        return Response(status_code=404)

    def _handle_email_view(self, email_id: str) -> HTMLResponse:
        """Fallback for text emails"""
        return HTMLResponse(f"""
            <html>
                <body>
                    <h1>Email Preview</h1>
                    <p>Email ID: {email_id}</p>
                    <img src="https://yourdomain.com/track/view_{email_id}" width="1" height="1">
                </body>
            </html>
        """)

    def _log_open_event(self, metadata: dict):
        """Log open event to your database"""
        # Implement your actual logging here
        print(f"Email opened: {metadata}")

    def deliver(self, message: str, recipient: str, method: str, **kwargs) -> dict:
        """Send message with tracking"""
        if method == "email":
            email_id = kwargs.get('email_id', str(uuid.uuid4()))
            pixel_url = self._generate_pixel_url(email_id, kwargs['lead_id'])
            
            if kwargs.get('is_html', False):
                message = message.replace('{tracking_pixel}', 
                    f'<img src="{pixel_url}" width="1" height="1" style="display:none">')
            else:
                message += f"\n\nView online: {pixel_url.replace('/track/','/view/')}"
            
            # Your actual email sending logic here
            print(f"Sending email to {recipient} with tracking")
            try:
            if method == "email":
                return self._send_email(
                    body=message,
                    to_email=recipient,
                    subject=kwargs.get("subject", "Follow Up")
                )
            elif method == "slack":
                return self._send_slack(
                    text=message,
                    channel_id=recipient  # Slack channel ID
                )
            else:
                raise ValueError(f"Unknown method: {method}")
                
            except Exception as e:
                self.logger.error(f"Delivery failed: {str(e)}")
                self._fallback_log(message, recipient, method)
                return False
            
            return {
                'delivered': True,
                'email_id': email_id,
                'pixel_url': pixel_url
            }
        # Other methods (Slack, etc)
        return {'delivered': False}

    def _send_email(self, body: str, to_email: str, subject: str) -> bool:
        """Send email via SMTP"""
        try:
            # Configure from environment variables
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", 587))
            username = os.getenv("SMTP_USERNAME")
            password = os.getenv("SMTP_PASSWORD")
            
            if not all([username, password]):
                raise ValueError("SMTP credentials not configured")
            
            msg = MIMEMultipart()
            msg["From"] = username
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
                
            self.logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Email failed: {str(e)}")
            raise  # Re-raise for outer exception handling

    def _send_slack(self, text: str, channel_id: str) -> bool:
        """Send message to Slack channel"""
        try:
            client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
            response = client.chat_postMessage(
                channel=channel_id,
                text=text
            )
            self.logger.info(f"Slack message sent to {channel_id}")
            return response["ok"]
            
        except SlackApiError as e:
            self.logger.error(f"Slack API error: {e.response['error']}")
            raise
        except Exception as e:
            self.logger.error(f"Slack failed: {str(e)}")
            raise

    def _fallback_log(self, message: str, recipient: str, method: str) -> None:
        """Local fallback when delivery fails"""
        log_entry = (
            f"FAILED {method.upper()} TO: {recipient}\n"
            f"MESSAGE: {message}\n"
            f"TIMESTAMP: {self._current_timestamp()}\n"
            "="*50
        )
        self.logger.warning(log_entry)
        
        # Also write to dedicated fallback file
        with open("data/notifier_fallback.log", "a") as f:
            f.write(log_entry + "\n")

    def _setup_logging(self) -> None:
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("data/notifier.log")
            ]
        )

    def _current_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()

# Example usage
if __name__ == "__main__":
    notifier = Notifier()
    
    # Test email (will fail without .env configured)
    notifier.deliver(
        message="Test message body",
        recipient="test@example.com",
        method="email",
        subject="Test Subject"
    )
    
    # Test fallback logging
    notifier.deliver(
        message="This will log to fallback",
        recipient="invalid@example.com",
        method="email"
    )
