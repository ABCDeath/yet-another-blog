#### Выполнено:
* Добавление пользователей через админку;
* Просмотр, создание, редактирование и удаление постов (пост содержит заголовок, текст и автоматически заполняемую при сохранении дату):
  * Через админку;
  * Через интерфейс сайта;
* Возможность пользователя подписаться на других пользователей и управление подписками;
* Лента пользователя с постами от тех, на кого он подписан:
  * Если не логиниться или нет подписок, можно читать посты всех пользователей по отдельному url;
  * Возможность отметить пост прочитанным (текст поста в ленте будет сокращен), отметку можно снять;
  * При отписке информация о прочитанных постах удаляется;
* При появлении нового поста (через интерфейс или админку) выполняется рассылка на email всем подписчикам со ссылкой на пост;
* Тесты:
  * Тесты моделей;
  * Тесты View для отображения информации.
