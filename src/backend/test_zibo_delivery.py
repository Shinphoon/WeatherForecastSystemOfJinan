import unittest
from unittest.mock import patch, MagicMock
import email_service
import zibo_products
from fastapi import HTTPException

class DeliveryTests(unittest.TestCase):
    def test_gmail_sender_accepts_other_recipient_domains(self):
        env={'GMAIL_SENDER_EMAIL':'sender@gmail.com','GMAIL_APP_PASSWORD':'test-only', 'SMTP_HOST':'unused.invalid'}
        with patch.dict('os.environ',env,clear=True), patch.object(email_service.smtplib,'SMTP_SSL') as smtp:
            for domain in ['qq.com','126.com','163.com','gmail.com']:
                email_service.send_briefing_email('recipient@'+domain,'测试','测试内容')
                msg=smtp.return_value.send_message.call_args.args[0]
                self.assertEqual(msg['To'],'recipient@'+domain)
                self.assertIn('sender@gmail.com',msg['From'])
                self.assertEqual(smtp.call_args.args, ('smtp.gmail.com',465))
    def test_proxy_rejects_arbitrary_paths(self):
        with patch.object(zibo_products.requests,'get') as request:
            for day,file in [('20260918','../../secret'),('20260918','370300_pre_20260918140000_20260919150000.png')]:
                with self.assertRaises(HTTPException): zibo_products.zibo_product(day,file)
            request.assert_not_called()
    def test_proxy_validates_and_caches_png(self):
        zibo_products.cache.clear()
        response=MagicMock();response.status_code=200
        response.iter_content.return_value=[b'\x89PNG\r\n\x1a\ntest']
        with patch.object(zibo_products.requests,'get') as request:
            request.return_value.__enter__.return_value=response
            for _ in range(2):
                result=zibo_products.zibo_product('20260918','370300_pre_20260918140000_20260918150000.png')
                self.assertEqual(result.media_type,'image/png')
            self.assertEqual(request.call_count,1)

if __name__=='__main__': unittest.main()
