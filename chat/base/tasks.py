# from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer
# from chat.base.models import MessageModel
# from comptes.models import CustomFCMDevice
# from notifications.base.models import NotificationSettings, Notifications
# from Qaryb_API.celery import app
#
#
# class GetAppIconBadges:
#
#     @staticmethod
#     def get_users_from_conversation(user_pk):
#         my_set = set()
#         result_msg_recipient = MessageModel.objects.filter(recipient__pk=user_pk)
#         for i in result_msg_recipient:
#             if i.viewed is False:
#                 my_set.add(i.user.pk)
#         return len(my_set)
#
#     def get_badges(self, user_pk):
#         unread_conversations = self.get_users_from_conversation(user_pk)
#         unread_notifications = Notifications.objects.filter(user__pk=user_pk, viewed=False).count()
#         return unread_conversations + unread_notifications
#
#
# class NotifyMessageReceivedTaskV2(app.Task):
#     name = "Qaryb_API_dev.chat.v2_0_0.tasks.NotifyMessageReceivedTaskV2"
#
#     @staticmethod
#     def notify_message_received_task(id_, user_id, recipient_id, body, attachment,
#                                      first_name, last_name):
#         event = {
#             'type': 'recieve_group_message',
#             'message': {
#                 "type": "message",
#                 "id": id_,
#                 "initiator": user_id,
#                 "recipient": recipient_id,
#                 "click_action": "FLUTTER_NOTIFICATION_CLICK",
#                 "fln_body": body,
#                 "fln_title": first_name + ' ' + last_name,
#             }
#         }
#
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)("%s" % recipient_id, event)
#         user_notification_settings = NotificationSettings.objects.get(user=recipient_id)
#         if user_notification_settings.push_messages:
#             devices = CustomFCMDevice.objects.filter(user=recipient_id)
#             app_badges = GetAppIconBadges()
#             badges = app_badges.get_badges(recipient_id)
#             for device in devices:
#                 if device.active:
#                     if attachment is not None:
#                         if device.lang == 'en':
#                             body = 'Picture'
#                         elif device.lang == 'fr':
#                             body = 'Photo'
#                         else:
#                             body = 'صورة'
#                         event['message']['fln_body'] = body
#                     device.send_message(title=first_name + ' ' + last_name,
#                                         sound='default',
#                                         badge=badges,
#                                         body=body,
#                                         icon="qaryb_logo",
#                                         data=event['message'],
#                                         color="#004afb")
#
#     def run(self, id_, user_id, recipient_id, body, attachment, first_name, last_name):
#         self.notify_message_received_task(id_, user_id, recipient_id, body, attachment,
#                                           first_name, last_name)
#
#
# app.tasks.register(NotifyMessageReceivedTaskV2())
