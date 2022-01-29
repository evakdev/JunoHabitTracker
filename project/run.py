import base
from controllers.start import Start
from controllers.errorhandler import error_handler


def recreate_database():

    base.Base.metadata.drop_all(base.engine)
    base.Base.metadata.create_all(base.engine)
    table_list = base.engine.table_names()
    print("Tables:")
    for table in table_list:
        print(f"     {table}")


def main():
    start_menu = Start()

    base.dispatcher.add_handler(start_menu.handler)
    base.dispatcher.add_error_handler(error_handler)

    # recreate_database()
    base.updater.start_polling()
    base.updater.idle()


if __name__ == "__main__":
    main()
