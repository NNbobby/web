document.addEventListener('DOMContentLoaded', () => {
    const openModalButtons = document.querySelectorAll('[data-modal]'); // Кнопки с атрибутом data-modal
    const closeModalButtons = document.querySelectorAll('.close-modal'); // Кнопки "закрыть"
    const allModals = document.querySelectorAll('.modal'); // Все модальные окна

    // Открытие модального окна
    openModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modalId = button.getAttribute('data-modal'); // Берём ID модалки
            const modal = document.getElementById(modalId); // Находим её
            if (modal) {
                modal.classList.remove('hidden'); // Убираем класс hidden
            }
        });
    });

    // Закрытие модального окна (по кнопке "крестик")
    closeModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal'); // Ближайшая модалка
            if (modal) {
                modal.classList.add('hidden'); // Добавляем hidden назад
            }
        });
    });

    // Закрытие модального окна по клику на фон (не на содержимое)
    allModals.forEach(modal => {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) { // Проверяем, если клик на фон
                modal.classList.add('hidden'); // Скрываем окно
            }
        });
    });
});
