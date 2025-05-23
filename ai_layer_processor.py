import json
import os

from pdfminer.high_level import extract_text
from pyspark.sql.functions import col, regexp_replace, trim, monotonically_increasing_id, row_number, lit
from pyspark.sql.types import StructType, StructField, StringType, MapType, LongType
from pyspark.sql.window import Window

from .ai_embedding import AiEmbedding
from .ai_storage import AiStorage
from .ai_utils import AiUtils
from .splitters.ai_json_splitter import AiJsonSplitter
from .splitters.ai_markdown_splitter import AiMarkdownSplitter
from .splitters.ai_open_api_splitter import AiOpenApiSplitter
from .splitters.ai_text_splitter import AiTextSplitter
from .splitters.split_document import SplitDocument


#################################################
# AiLayerProcessor
#################################################
class AiLayerProcessor:
    LANDING_PATH = "landing"
    BRONZE_PATH = "bronze"
    SILVER_PATH = "silver"
    GOLD_PATH = "gold"

    def __init__(self, catalog: str, spark, bucket):
        super().__init__()
        self.catalog = catalog
        self.spark = spark
        self.bucket = bucket

    def get_newest_folder(self, full_path: str, extraction_date: str = ""):
        if extraction_date != "":
            return AiUtils.define_extraction_path(category=full_path, extraction_date=extraction_date)

        list = self.storage.list_path(full_path, type="PATH")

        ordered_list = sorted(list, key=lambda item: item['name'], reverse=True)

        if len(ordered_list) > 0:
            return ordered_list[0]["name"]
        else:
            print("Nenhuma pasta encontrada: " + full_path)
            return None

    def delete_table(self, category: str, sulfix: str) -> str:
        if self.spark.sql(f"SHOW schemas IN {self.catalog} LIKE '{category}'").count() > 0:
            catalog_schema = f"{self.catalog}.{category}"
            tables_df = self.spark.sql(f"show tables in {catalog_schema}")

            table_name_list = [row.tableName for row in tables_df.collect() if row.tableName.lower().endswith("_" + sulfix)]

            for t_name in table_name_list:
                self.spark.sql(f"DROP TABLE IF EXISTS {catalog_schema}.{t_name}")

    def save_as_delta(self, df, category: str, sub_category: str, sulfix: str, mode: str = "overwrite") -> str:
        """
        Salva o DataFrame como uma tabela Delta.
        """
        table_name = f"{self.catalog}.{category}.{sub_category}_" + sulfix
 
        self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{category};")
        self.spark.sql(f"CREATE DATABASE IF NOT EXISTS {self.catalog}.{category};")
        
        df.write.format("delta").mode(mode).saveAsTable(table_name)

        return table_name


#################################################
# AiLandingToBronzeProcessor
#################################################
class AiLandingToBronzeProcessor(AiLayerProcessor):
    def __init__(self, catalog: str, spark, storage: AiStorage, context_size:int = 0, chunck_size: int = 1000, chunck_overlap: int = 200):
        super().__init__(catalog, spark, storage.get_base_path())
        self.storage = storage
        self.context_size = context_size
        self.chunck_size = chunck_size
        self.chunck_overlap = chunck_overlap

    def process(self, category_obj, extraction_date: str = "", has_extraction_path: bool = True, append: bool = False):
        category_list = None
        if isinstance(category_obj, list):
            category_list = category_obj
        else:
            category_list = [category_obj]

        df_tables = []

        for category in category_list:

            full_path = AiLayerProcessor.LANDING_PATH + "/" + category
            if has_extraction_path:
                full_path = self.get_newest_folder(full_path, extraction_date)
            
            print("folder: " + full_path)

            if full_path is not None:
                sub_category_list = self.storage.list_path(full_path, type="PATH")

                # Cria um DataFrame Spark a partir da lista de dados
                schema = StructType([
                    StructField("id", StringType(), nullable=True),
                    StructField("content", StringType(), nullable=False),
                    StructField("content_to_embed", StringType(), nullable=False),
                    StructField("metadata", MapType(StringType(), StringType()), nullable=False),
                    StructField("file_key", StringType(), nullable=False)
                ])

                self.delete_table(category=category, sulfix=AiLayerProcessor.BRONZE_PATH)

                print("sub_category_list: " + str(len(sub_category_list)))
                for sub_category in sub_category_list:
                    file_list = self.storage.list_path(sub_category["name"], type="FILE")
                    data = []
                    sub = os.path.basename(sub_category["name"])

                    for file in file_list:
                        text = None
                        splitter = None
                        if file["name"].lower().endswith(".pdf"):
                            text = self.extract_pdf_to_text("", file["name"])
                            splitter = AiTextSplitter(
                                chunk_size=self.chunck_size,
                                # Tamanho máximo do chunk em caracteres ou tokens aproximados
                                chunk_overlap=self.chunck_overlap  # Sobreposição entre chunks
                            )
                        elif file["name"].lower().endswith(".txt"):
                            text = self.extract_text(file["name"])
                            splitter = AiTextSplitter(
                                context_size=self.context_size,
                                chunk_size=self.chunck_size,
                                # Tamanho máximo do chunk em caracteres ou tokens aproximados
                                chunk_overlap=self.chunck_overlap  # Sobreposição entre chunks
                            )
                        elif file["name"].lower().endswith(".md"):
                            text = self.extract_text(file["name"])
                            splitter = AiMarkdownSplitter(
                                context_size=self.context_size,
                                chunk_size=self.chunck_size,
                                # Tamanho máximo do chunk em caracteres ou tokens aproximados
                                chunk_overlap=self.chunck_overlap  # Sobreposição entre chunks
                            )
                        elif file["name"].lower().endswith(".json"):
                            text = self.extract_text(file["name"])
                            if '"openapi":' in text:
                                splitter = AiOpenApiSplitter()
                            else:
                                splitter = AiJsonSplitter(
                                    context_size=self.context_size
                                )
                        else:
                            print("Formato de arquivo não suportado: " + file["name"])

                        if text is None:
                            continue

                        metadata_path = (file["name"][:-len(os.path.basename(file["name"]))]) + "/.metadata/"
                        metadata_name = os.path.basename(file["name"]) + ".metadata"
                        metadata_json_default = self.storage.download_fileobj("", metadata_path + metadata_name)

                        metadata = None
                        if metadata_json_default is not None:
                            metadata = json.loads(metadata_json_default)
                        else:
                            metadata = {}

                        metadata["file_key"] = file["name"].split('/')[-1]
                        metadata["category"] = category
                        metadata["sub_category"] = sub

                        document_list = splitter.create_documents(text, metadata)

                        # Adiciona cada bloco como uma linha no DataFrame
                        for document in document_list:
                            content = document.page_content.strip()
                            content_to_embed = content
                            if isinstance(document, SplitDocument):
                                content_to_embed = document.content_to_embed

                            data.append({"id": None,
                                         "content": content,
                                         "content_to_embed": content_to_embed,
                                         "metadata": document.metadata,
                                         "file_key": document.metadata["file_key"]
                                         })

                        print("Arquivo processado: " + file["name"])

                    file_df = self.spark.createDataFrame(data, schema=schema)

                    file_df = file_df.withColumn(
                        "content",
                        # Remove múltiplos espaços consecutivos
                        regexp_replace(
                            # Remove espaços no início e fim
                            trim(col("content")),
                            "\\s+", " "
                        )
                    )

                    file_df = file_df.withColumn(
                        "content",
                        # Converte caracteres Unicode de espaço para espaço normal (incluindo NBSP, tabs, etc)
                        regexp_replace(col("content"),
                                       "[\\u00A0\\u1680\\u180E\\u2000-\\u200B\\u202F\\u205F\\u3000\\uFEFF\\t\\n\\r\\f\\v]",
                                       " ")
                    )

                    # Adiciona ID sequencial
                    window_spec = Window.orderBy(monotonically_increasing_id())
                    final_df = file_df.withColumn("id", row_number().over(window_spec))

                    table_name = self.save_as_delta(df=final_df, category=category, sub_category=sub,
                                                    sulfix=AiLayerProcessor.BRONZE_PATH,
                                                    mode=("append" if (append) else "overwrite"))

                    df_tables.append(table_name)

                    print(f"Total de registros processados: {final_df.count()}")

                    print("Tabela criada: " + table_name)

        return df_tables

    def extract_pdf_to_text(self, file_path: str, file_name: str) -> str:
        temp_file_path = None
        try:
            temp_file_path = self.storage.download_file(file_path, file_name)

            try:
                # Extrai o texto com codificação UTF-8
                text = extract_text(temp_file_path, codec="utf-8")

                return text
            except Exception as e:
                print(f"Erro ao extrair texto com pdfminer.six: {e}")
                return None
            finally:
                # Remove o arquivo temporário
                os.remove(temp_file_path)
        except Exception as e:
            print(f"Erro ao processar o arquivo {file_name}: {e}")
            return None
        finally:

            if temp_file_path is not None and os.path.exists(temp_file_path):
                os.remove(temp_file_path)  # Garante que o arquivo temporário seja removido em caso de erro

    def extract_text(self, file_name):
        try:
            text = self.storage.download_fileobj("", file_name)
            return text
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return None

   
#################################################
# AiBronzeToSilverProcessor
#################################################
class AiBronzeToSilverProcessor(AiLayerProcessor):
    def __init__(self, catalog: str, spark, bucket: str):
        super().__init__(catalog, spark, bucket)

    def process(self, category_obj, append: bool = False):

        category_list = None
        if isinstance(category_obj, list):
            category_list = category_obj
        else:
            category_list = [category_obj]

        df_tables = []

        for category in category_list:
            tables_df = self.spark.sql(f"show tables in {self.catalog}.{category}")

            # Extraia os nomes das tabelas do DataFrame
            table_names = [row.tableName for row in tables_df.collect() if
                           row.tableName.lower().endswith("_" + AiLayerProcessor.BRONZE_PATH)]

            self.delete_table(category=category, sulfix=AiLayerProcessor.SILVER_PATH)

            for table_name in table_names:
                data_frame = self.spark.sql(f"select * from {self.catalog}.{category}.{table_name}")
                # Define o nome do modelo embedding
                # Aplica a UDF ao dataframe para criar a nova coluna com embeddings
                chunked_df_with_embeddings = data_frame.withColumn("embedding", AiEmbedding.process_embeddings_udf(
                    col("content_to_embed")))

                # Para forçar a execução e verificar os resultados (usando collect() em vez de show() para debug inicial)
                print(
                    f"Processando: {table_name} - Total de registros processados: {chunked_df_with_embeddings.count()}")

                sub = table_name[:((len(AiLayerProcessor.BRONZE_PATH) + 1) * -1)]

                table_name_silver = self.save_as_delta(df=chunked_df_with_embeddings, category=category,
                                                       sub_category=sub, sulfix=AiLayerProcessor.SILVER_PATH,
                                                       mode=("append" if (append) else "overwrite"))

                df_tables.append(table_name_silver)
                print("Tabela criada: " + table_name_silver)

        return df_tables


#################################################
# AiSilverToGoldProcessor
#################################################
class AiSilverToGoldProcessor(AiLayerProcessor):
    def __init__(self, catalog: str, spark, bucket: str):
        super().__init__(catalog, spark, bucket)

    def process(self, category_obj, schema: str, table: str, append: bool = False):

        sulfix = AiLayerProcessor.GOLD_PATH
        df_gold = None
        table_exists = False
        max_id = 1
        if self.spark.catalog.tableExists(f"{self.catalog}.{schema}.{table}_{sulfix}"):
            table_exists = True
            df = self.spark.sql(f"select max(id) as max from {self.catalog}.{schema}.{table}_{sulfix}")
            max_id = df.collect()[0].max

        category_list = None
        if isinstance(category_obj, list):
            category_list = category_obj
        else:
            category_list = [category_obj]

        window_spec = Window.orderBy(monotonically_increasing_id())
        table_name = None

        total = 0
        for category in category_list:
            if table_exists or df_gold is not None:
                self.spark.sql(f"delete from {self.catalog}.{schema}.{table}_{sulfix} where category='{category}'")
                df_gold = self.spark.sql(f"select * from {self.catalog}.{schema}.{table}_{sulfix}")

            catalog_schema = f"{self.catalog}.{category}"

            tables_df = self.spark.sql(f"show tables in {catalog_schema}")
            # Extraia os nomes das tabelas do DataFrame
            table_name_list = [row.tableName for row in tables_df.collect() if
                               row.tableName.lower().endswith("_" + AiLayerProcessor.SILVER_PATH)]

            for table_name in table_name_list:

                df = self.spark.table(f"{catalog_schema}.{table_name}").select(
                    col("id").alias("id_silver"),
                    col("content"),
                    col("content_to_embed"),
                    col("metadata.category").alias("category"),
                    col("metadata.sub_category").alias("sub_category"),
                    col("metadata.information_security_label").alias("information_security_label"),
                    col("metadata.page").alias("page"),
                    col("metadata.file_key").alias("file_key"),
                    col("metadata.reference_url").alias("reference_url"),
                    col("metadata.position").alias("position"),
                    col("embedding"),
                    (row_number().over(window_spec) + lit(max_id)).cast(LongType()).alias("id"),
                    lit(f"{catalog_schema}.{table_name}").alias("table_name_silver")
                )

                total = total + df.count()
                if df_gold is None:
                    df_gold = df
                else:
                    df_gold = df_gold.unionByName(df)

            table_name = self.save_as_delta(df=df_gold, category=schema, sub_category=table, sulfix=sulfix,
                                            mode=("append" if (append) else "overwrite"))

        if not table_exists:
            print(f"Habilitando Change Data Feed na tabela {table_name}...")
            self.spark.sql(f"ALTER TABLE {table_name} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
            print("Change Data Feed habilitado com sucesso.")

        print(f"Total de registros processados: {total}")
        print("Tabela criada: " + table_name)
        return [table_name]
