from fastapi import FastAPI, Form
from bot_init import bot
import db_requests
import config
import datetime
import traceback




app = FastAPI()

async def send_message_to_admins(message_text: str):
    admins_ids = [admin.user_telegram_id for admin in await db_requests.get_admins()]
    for admin in admins_ids:
        try:
            await bot.send_message(admin, message_text)
        except:
            print(traceback.format_exc())


@app.post("/callback")
async def process_payment(
    date: str = Form(...),
    order_num: str = Form(...),
    sum: str = Form(...),
    payment_type: str = Form(...),
    payment_status: str = Form(...),
    payment_status_description: str = Form(...)
):
    order = await db_requests.get_order_by_id(int(order_num))
    user = await db_requests.get_user_by_id(order.user_id)
    now = datetime.datetime.utcnow()
    if payment_status == 'success':
        user_message_text = (f'✅ Оплата заказа прошла успешно\n\n'
                             f'Для вас открыт доступ к курсу <b>{order.course.title}</b>!\n'
                             f'Скорей приступайте к обучению!')
        message_text = (f'✅ Заказ <b>#{order.id}</b> успешно оплачен!\n\n'
                        f'<b>Дата оплаты:</b> {date}\n'
                        f'<b>Тип оплаты:</b> {payment_type} ({payment_status_description})\n'
                        f'<b>Оплаченный курс:</b> {order.course.title}\n'
                        f'<b>Стоимость:</b> {sum}\n'
                        f'<b>Ученик:</b> {user.user_name} (<code>+{user.phone_number}</code>)')
        await db_requests.change_order_payment_status(order.id, True)
        await db_requests.add_course_to_user(user.id, order.course.id, now)
        try:
            await bot.send_message(user.user_telegram_id, user_message_text)
        except:
            await send_message_to_admins('Ошибка отправки сообщения пользователю. Подробности в логах бота.')
        await send_message_to_admins(message_text)
    
    elif payment_status == 'order_approved':
        message_text = (f'✅ Заявка на рассрочку по заказу <b>#{order.id}</b> одобрена!\n\n'
                        f'<b>Тип оплаты:</b> {payment_type} ({payment_status_description})\n'
                        f'<b>Курс:</b> {order.course.title}\n'
                        f'<b>Стоимость:</b> {sum}\n'
                        f'<b>Ученик:</b> {user.user_name} (+{user.phone_number})')
        await send_message_to_admins(message_text)
    
    elif payment_status == 'order_canceled':
        message_text = (f'❌ Заявка на рассрочку по заказу <b>#{order.id}</b> отменена клиентом!\n\n'
                        f'<b>Тип оплаты:</b> {payment_type} ({payment_status_description})\n'
                        f'<b>Курс:</b> {order.course.title}\n'
                        f'<b>Стоимость:</b> {sum}\n'
                        f'<b>Ученик:</b> {user.user_name} (+{user.phone_number})')
        await send_message_to_admins(message_text)
    
    elif payment_status == 'order_denied':
        message_text = (f'❌ Оплата заказа <b>#{order.id}</b> отклонена банком.\n\n'
                        f'<b>Тип оплаты:</b> {payment_type} ({payment_status_description})\n'
                        f'<b>Курс:</b> {order.course.title}\n'
                        f'<b>Стоимость:</b> {sum}\n'
                        f'<b>Ученик:</b> {user.user_name} (+{user.phone_number})')
        await send_message_to_admins(message_text)


    return {"message": "OK"}
