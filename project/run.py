import base
import main


def recreate_database():

    base.Base.metadata.drop_all(base.engine)
    base.Base.metadata.create_all(base.engine)
    table_list=base.engine.table_names()
    print("Tables:")
    for table in table_list:
        print(f"     {table}")


recreate_database()
base.updater.start_polling()
