#-*- encoding:utf-8 -*-
import json
import unittest
import mock

from kakaoplus import kakaoplus as KaKao
from flask import Flask

class KaKaoTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.agent = KaKao.KaKaoAgent(self.app, '/')

    def test_handle_webhook(self):
        req = {"user_key": "testID", "type": "text", "content": "test"}
        counter = mock.MagicMock()

        @self.agent.handle_message
        def default_handler(req, res):
            self.assertTrue(req.recieved_text)
            self.assertFalse(req.recieved_photo)
            self.assertEqual(req.user_key, "testID")
            self.assertEqual(req.content, "test")
            self.assertIsNone(res.text)
            self.assertIsNone(res.photo)
            self.assertIsNone(res.message_button)
            self.assertIsNone(res.keyboard_buttons)

            res.text = '귀하의 차량이 성공적으로 등록되었습니다. 축하합니다!'
            res.photo = {
                'url': 'https://photo.src',
                'width': 640,
                'height': 480
            }
            res.message_button = {
                'label': '주유 쿠폰받기',
                'url': 'https://coupon/url'
            }
            res.keyboard_buttons = [
                '처음으로',
                '다시 등록하기',
                '취소하기'
            ]
            counter()

        with self.app.test_client() as c:
            rv = c.post('/message', data=json.dumps(req),
                        content_type='application/json')
            self.assertEquals(
                rv.get_data(as_text=True),
                json.dumps({
                    "message": {
                        "message_button": {
                            "label": "주유 쿠폰받기",
                            "url": "https://coupon/url"
                        },
                        "photo": {
                            "url": "https://photo.src",
                            "width": 640,
                            "height": 480
                        },
                        "text": "귀하의 차량이 성공적으로 등록되었습니다. 축하합니다!"
                    },
                    "keyboard": {
                        "buttons": [
                            "처음으로",
                            "다시 등록하기",
                            "취소하기"
                        ],
                        "type": "buttons"
                    }
                }, sort_keys=True)
            )
            self.assertEquals(1, counter.call_count)

        req2 = {"user_key": "testID", "type": "text", "content": "hi my name is yo"}
        counter2 = mock.MagicMock()

        @self.agent.handle_message(['(hi).*'])
        def greeting_test(req, res):
            self.assertTrue(req.recieved_text)
            self.assertFalse(req.recieved_photo)
            self.assertEqual(req.user_key, "testID")
            self.assertEqual(req.content, 'hi my name is yo')

            res.text = 'Regular Expression start with hi'
            counter2()

        with self.app.test_client() as c:
            rv = c.post('/message', data=json.dumps(req2),
                        content_type='application/json')
            self.assertEquals(1, counter2.call_count)
            self.assertEqual(
                rv.get_data(as_text=True),
                json.dumps({
                    'keyboard': {'type': 'text'},
                    'message': {'text': 'Regular Expression start with hi'}
                }, sort_keys=True)
            )

    def test_handle_keyboard(self):
        @self.agent.handle_keyboard
        def keyboard_handler(res):
            self.assertIsNone(res.keyboard_buttons)
            res.keyboard_buttons = [
                'test button1',
                'test button2',
                'test button3'
            ]
        with self.app.test_client() as c:
            rv = c.get('/keyboard')
            self.assertEqual(
                json.loads(rv.get_data(as_text=True)),
                {
                    "buttons": [
                        'test button1',
                        'test button2',
                        'test button3'
                    ],
                    "type": "buttons"
                })

    def test_handle_text_keyboard(self):
        with self.app.test_client() as c:
            rv = c.get('/keyboard')
            self.assertEqual(
                json.loads(rv.get_data(as_text=True)),
                {
                    "type": "text"
                })

    def test_photo_handler(self):
        req = {"user_key": "testID", "type": "photo", "content": "image.png"}
        counter = mock.MagicMock()
        @self.agent.handle_photo
        def photo_handler(req, res):
            self.assertTrue(req.recieved_photo)
            self.assertFalse(req.recieved_text)
            self.assertEqual(req.user_key, "testID")
            self.assertEqual(req.content, "image.png")
            self.assertIsNone(res.text)
            self.assertIsNone(res.photo)
            self.assertIsNone(res.message_button)
            self.assertIsNone(res.keyboard_buttons)
            counter()

        with self.app.test_client() as c:
            rv = c.post('/message', data=json.dumps(req),
                       content_type='application/json')
            self.assertEqual(rv.get_data(as_text=True), 'ok')

    def test_no_handler(self):
        req = {"user_key": "testID", "type": "text", "content": "test"}
        with self.app.test_client() as c:
            rv = c.post('/message', data=json.dumps(req),
                        content_type='application/json')
            self.assertEqual(rv.get_data(as_text=True), "ok")

    def test_no_matching_type(self):
        req = {"user_key": "testID", "type": "unknown"}
        with self.app.test_client() as c:
            rv = c.post('/message', data=json.dumps(req),
                        content_type='application/json')
            self.assertEqual(rv.get_data(as_text=True), "ok")