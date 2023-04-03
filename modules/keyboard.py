from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from modules.variables import boost_enabled
def fast_keyboard(num):
    """Быстро назначить клавиатуру: \n
        0 - Добавить кнопки для проверки постов \n
        1 - Добавить кнопку "вернуться" \n
        2 - Главное меню беседы проверка \n
        3 - Меню параметры \n
        4 - Личное меню \n
        5 - Кнопка "абобус регистрация" \n
        6 - Кнопка "СТОП"
        7 - Личное меню с незареганной основой \n
        8 - Меню с подпиской.
        9 - кнопка Главное меню
        10 - сабменю по кнопке проверка
        """
    if num == 0:
        keyboard = VkKeyboard(inline=True)
        keyboard.add_button('Принять', VkKeyboardColor.POSITIVE)
        keyboard.add_button('Отклонить', VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('Прекратить проверку')
        return keyboard
    if num == 1:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Вернуться', VkKeyboardColor.NEGATIVE)
        return keyboard
    if num == 2:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('/Проверка', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('/Параметры', VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('/Объявление',
                            VkKeyboardColor.SECONDARY)
        return keyboard
    if num == 3:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Список админов', VkKeyboardColor.SECONDARY)
        keyboard.add_button('Список всех', VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('Список премиумов', VkKeyboardColor.SECONDARY)
        keyboard.add_button('Список зарегистрированных', VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('Назначить статус BASIC', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Назначить статус PREMIUM', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Назначить статус HELPER', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Назначить посты', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Обновить базу юзеров', VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        if boost_enabled() == True:
            keyboard.add_button('Выключить буст', VkKeyboardColor.NEGATIVE)
            keyboard.add_line()
        else:
            keyboard.add_button('Включить буст', VkKeyboardColor.POSITIVE)
            keyboard.add_line()
        keyboard.add_button('Закрыть параметры', VkKeyboardColor.NEGATIVE)
        return keyboard
    if num == 4:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Регистрация', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Мой профиль', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Спасительная кнопка', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Список аккаунтов', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Дополнительные команды', VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('Выйти из аккаунта', VkKeyboardColor.NEGATIVE)
        return keyboard
    if num == 5:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Регистрация', VkKeyboardColor.PRIMARY)
        return keyboard
    if num == 6:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('СТОП', VkKeyboardColor.NEGATIVE)  # задать кнопку STOP на клавиатуре
        return keyboard
    if num == 7:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Регистрация', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Спасительная кнопка', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Список аккаунтов', VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Дополнительные команды', VkKeyboardColor.SECONDARY)
        return keyboard
    if num == 8:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Приобрести подписку', VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('Главное меню', VkKeyboardColor.NEGATIVE)
        return keyboard
    if num == 9:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Главное меню', VkKeyboardColor.NEGATIVE)
        return keyboard

    if num == 10:
        keyboard = VkKeyboard(inline=False)
        keyboard.add_button('Проверка постов', VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('Вернуться', VkKeyboardColor.NEGATIVE)
        return keyboard



