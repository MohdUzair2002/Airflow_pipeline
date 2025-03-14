from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from validate_all_tables_dag import (validate_brands, validate_categories, validate_customers,
    validate_orders, validate_order_items, validate_products, validate_staffs,
    validate_stocks, validate_stores)
import pandas as pd
import os
import boto3
from io import StringIO

# S3 Configuration
S3_BUCKET = 'airflow-pipeline-s3-1'
AWS_ACCESS_KEY_ID = 'AKIA3M7ACNA3Q4WYNGXZ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION = 'eu-north-1'

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def read_csv_from_s3(bucket, key):
    """Read CSV file from S3 bucket."""
    try:
        # Get object from S3
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        # Read CSV content
        return pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))
    except Exception as e:
        print(f'Error reading {key} from S3: {str(e)}')
        raise

def analyze_category_sales():
    """Analyze sales data by category using validated data."""
    try:
        # Read the necessary data from S3
        categories_df = read_csv_from_s3(S3_BUCKET, 'categories.csv')
        products_df = read_csv_from_s3(S3_BUCKET, 'products.csv')
        order_items_df = read_csv_from_s3(S3_BUCKET, 'order_items.csv')
        
        # Verify required columns exist
        required_columns = {
            'categories': ['category_id', 'category_name'],
            'products': ['product_id', 'category_id', 'list_price'],
            'order_items': ['product_id', 'quantity', 'list_price', 'discount']
        }
        
        for df_name, columns in required_columns.items():
            df = {'categories': categories_df, 'products': products_df, 'order_items': order_items_df}[df_name]
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f'Missing required columns in {df_name}: {missing_cols}')
        
        # Merge data to get category information
        product_categories = products_df.merge(categories_df, on='category_id', how='inner')
        sales_data = order_items_df.merge(product_categories, on='product_id', how='inner')
        
        # Calculate sales metrics by category
        sales_data['sale_amount'] = sales_data['quantity'] * sales_data['list_price_x'] * (1 - sales_data['discount'])
        
        # Aggregate by category
        category_sales = sales_data.groupby('category_name').agg({
            'quantity': 'sum',
            'sale_amount': 'sum',
            'discount': 'mean'
        }).round(2)
        
        category_sales.columns = ['total_quantity', 'total_sales', 'avg_discount']
        
        # Save results to S3
        output_buffer = StringIO()
        category_sales.to_csv(output_buffer)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key='output/category_sales_analysis.csv',
            Body=output_buffer.getvalue()
        )
        print('Category sales analysis completed successfully')
    except Exception as e:
        print(f'Category sales analysis failed: {str(e)}')
        raise

def analyze_category_stocks():
    """Analyze stock levels by category using validated data."""
    try:
        # Read the necessary data from S3
        categories_df = read_csv_from_s3(S3_BUCKET, 'categories.csv')
        products_df = read_csv_from_s3(S3_BUCKET, 'products.csv')
        stocks_df = read_csv_from_s3(S3_BUCKET, 'stocks.csv')
        
        # Verify required columns exist
        required_columns = {
            'categories': ['category_id', 'category_name'],
            'products': ['product_id', 'category_id'],
            'stocks': ['store_id', 'product_id', 'quantity']
        }
        
        for df_name, columns in required_columns.items():
            df = {'categories': categories_df, 'products': products_df, 'stocks': stocks_df}[df_name]
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f'Missing required columns in {df_name}: {missing_cols}')
        
        # Merge data to get category information
        product_categories = products_df.merge(categories_df, on='category_id', how='inner')
        stock_data = stocks_df.merge(product_categories, on='product_id', how='inner')
        
        # Calculate stock metrics by category
        category_stocks = stock_data.groupby('category_name').agg({
            'quantity': 'sum',
            'store_id': 'nunique',
            'product_id': 'nunique'
        }).round(2)
        
        category_stocks.columns = ['total_quantity', 'store_coverage', 'unique_products']
        
        # Save results to S3
        output_buffer = StringIO()
        category_stocks.to_csv(output_buffer)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key='output/category_stocks_analysis.csv',
            Body=output_buffer.getvalue()
        )
        print('Category stocks analysis completed successfully')
    except Exception as e:
        print(f'Category stocks analysis failed: {str(e)}')
        raise

def analyze_product_sales():
    """Analyze sales data by product using validated data."""
    try:
        # Read the necessary data from S3
        products_df = read_csv_from_s3(S3_BUCKET, 'products.csv')
        order_items_df = read_csv_from_s3(S3_BUCKET, 'order_items.csv')
        
        # Verify required columns exist
        required_columns = {
            'products': ['product_id', 'product_name', 'list_price'],
            'order_items': ['product_id', 'quantity', 'list_price', 'discount']
        }
        
        for df_name, columns in required_columns.items():
            df = {'products': products_df, 'order_items': order_items_df}[df_name]
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f'Missing required columns in {df_name}: {missing_cols}')
        
        # Merge data to get product information
        sales_data = order_items_df.merge(products_df, on='product_id', how='inner')
        
        # Calculate sales metrics by product
        sales_data['sale_amount'] = sales_data['quantity'] * sales_data['list_price_x'] * (1 - sales_data['discount'])
        
        # Aggregate by product
        product_sales = sales_data.groupby(['product_id', 'product_name']).agg({
            'quantity': 'sum',
            'sale_amount': 'sum',
            'discount': 'mean'
        }).round(2)
        
        product_sales.columns = ['total_quantity', 'total_sales', 'avg_discount']
        
        # Save results to S3
        output_buffer = StringIO()
        product_sales.to_csv(output_buffer)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key='output/product_sales_analysis.csv',
            Body=output_buffer.getvalue()
        )
        print('Product sales analysis completed successfully')
    except Exception as e:
        print(f'Product sales analysis failed: {str(e)}')
        raise

def analyze_product_stocks():
    """Analyze stock levels by product using validated data."""
    try:
        # Read the necessary data from S3
        products_df = read_csv_from_s3(S3_BUCKET, 'products.csv')
        stocks_df = read_csv_from_s3(S3_BUCKET, 'stocks.csv')
        
        # Verify required columns exist
        required_columns = {
            'products': ['product_id', 'product_name'],
            'stocks': ['store_id', 'product_id', 'quantity']
        }
        
        for df_name, columns in required_columns.items():
            df = {'products': products_df, 'stocks': stocks_df}[df_name]
            missing_cols = [col for col in columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f'Missing required columns in {df_name}: {missing_cols}')
        
        # Merge data to get product information
        stock_data = stocks_df.merge(products_df, on='product_id', how='inner')
        
        # Calculate stock metrics by product
        product_stocks = stock_data.groupby(['product_id', 'product_name']).agg({
            'quantity': 'sum',
            'store_id': 'nunique'
        }).round(2)
        
        product_stocks.columns = ['total_quantity', 'store_coverage']
        product_stocks['avg_stock_per_store'] = (product_stocks['total_quantity'] / product_stocks['store_coverage']).round(2)
        
        # Save results to S3
        output_buffer = StringIO()
        product_stocks.to_csv(output_buffer)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key='output/product_stocks_analysis.csv',
            Body=output_buffer.getvalue()
        )
        print('Product stocks analysis completed successfully')
    except Exception as e:
        print(f'Product stocks analysis failed: {str(e)}')
        raise

# Default arguments for both DAGs
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 3, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Weekly Category Analysis DAG
with DAG(
    'weekly_category_analysis',
    default_args=default_args,
    description='Weekly category-level sales and stock analysis',
    schedule_interval='0 13 * * 3',  # Run at 1 PM every Wednesday
    catchup=False
) as category_dag:
    # Create validation tasks within the DAG context
    validate_brands_task = PythonOperator(
        task_id='brands',
        python_callable=validate_brands,
        dag=category_dag
    )

    validate_categories_task = PythonOperator(
        task_id='categories',
        python_callable=validate_categories,
        dag=category_dag
    )

    validate_customers_task = PythonOperator(
        task_id='customers',
        python_callable=validate_customers,
        dag=category_dag
    )

    validate_orders_task = PythonOperator(
        task_id='orders',
        python_callable=validate_orders,
        dag=category_dag
    )

    validate_order_items_task = PythonOperator(
        task_id='order_items',
        python_callable=validate_order_items,
        dag=category_dag
    )

    validate_products_task = PythonOperator(
        task_id='products',
        python_callable=validate_products,
        dag=category_dag
    )

    validate_staffs_task = PythonOperator(
        task_id='staffs',
        python_callable=validate_staffs,
        dag=category_dag
    )

    validate_stocks_task = PythonOperator(
        task_id='stocks',
        python_callable=validate_stocks,
        dag=category_dag
    )

    validate_stores_task = PythonOperator(
        task_id='stores',
        python_callable=validate_stores,
        dag=category_dag
    )

    category_sales_task = PythonOperator(
        task_id='category_sales_analysis',
        python_callable=analyze_category_sales,
        dag=category_dag
    )

    category_stocks_task = PythonOperator(
        task_id='category_stocks_analysis',
        python_callable=analyze_category_stocks,
        dag=category_dag
    )

    # Set up dependencies for validation tasks
    [validate_brands_task, validate_categories_task] >> validate_products_task
    validate_customers_task >> validate_orders_task
    [validate_products_task, validate_orders_task] >> validate_order_items_task
    validate_stores_task >> validate_stocks_task
    validate_products_task >> validate_stocks_task
    validate_stores_task >> validate_staffs_task

    # Set up dependencies for category analysis tasks
    [validate_categories_task, validate_products_task, validate_order_items_task] >> category_sales_task
    [validate_categories_task, validate_products_task, validate_stocks_task] >> category_stocks_task

# Daily Product Analysis DAG
with DAG(
    'daily_product_analysis',
    default_args=default_args,
    description='Daily product-level sales and stock analysis',
    schedule_interval='@daily',  # Run once every day
    catchup=False
) as product_dag:
    # Create validation tasks within the DAG context
    validate_brands_task = PythonOperator(
        task_id='brands',
        python_callable=validate_brands,
        dag=product_dag
    )

    validate_categories_task = PythonOperator(
        task_id='categories',
        python_callable=validate_categories,
        dag=product_dag
    )

    validate_customers_task = PythonOperator(
        task_id='customers',
        python_callable=validate_customers,
        dag=product_dag
    )

    validate_orders_task = PythonOperator(
        task_id='orders',
        python_callable=validate_orders,
        dag=product_dag
    )

    validate_order_items_task = PythonOperator(
        task_id='order_items',
        python_callable=validate_order_items,
        dag=product_dag
    )

    validate_products_task = PythonOperator(
        task_id='products',
        python_callable=validate_products,
        dag=product_dag
    )

    validate_staffs_task = PythonOperator(
        task_id='staffs',
        python_callable=validate_staffs,
        dag=product_dag
    )

    validate_stocks_task = PythonOperator(
        task_id='stocks',
        python_callable=validate_stocks,
        dag=product_dag
    )

    validate_stores_task = PythonOperator(
        task_id='stores',
        python_callable=validate_stores,
        dag=product_dag
    )

    product_sales_task = PythonOperator(
        task_id='product_sales_analysis',
        python_callable=analyze_product_sales,
        dag=product_dag
    )

    product_stocks_task = PythonOperator(
        task_id='product_stocks_analysis',
        python_callable=analyze_product_stocks,
        dag=product_dag
    )

    # Set up dependencies for validation tasks
    [validate_brands_task, validate_categories_task] >> validate_products_task
    validate_customers_task >> validate_orders_task
    [validate_products_task, validate_orders_task] >> validate_order_items_task
    validate_stores_task >> validate_stocks_task
    validate_products_task >> validate_stocks_task
    validate_stores_task >> validate_staffs_task

    # Set up dependencies for product analysis tasks
    [validate_products_task, validate_order_items_task] >> product_sales_task
    [validate_products_task, validate_stocks_task] >> product_stocks_task