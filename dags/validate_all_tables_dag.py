from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
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

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 3, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def validate_brands():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'brands.csv')
        
        assert not df.empty, "Brands data is empty"
        assert 'brand_id' in df.columns, "brand_id column is missing"
        assert 'brand_name' in df.columns, "brand_name column is missing"
        assert not df['brand_id'].isnull().any(), "Found null values in brand_id"
        assert not df['brand_name'].isnull().any(), "Found null values in brand_name"
        assert df['brand_id'].is_unique, "Duplicate brand IDs found"
        
        print(f"Validation successful. Found {len(df)} brand records.")
    except Exception as e:
        print(f"Error validating brands: {str(e)}")
        raise

def validate_categories():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'categories.csv')
        
        assert not df.empty, "Categories data is empty"
        assert 'category_id' in df.columns, "category_id column is missing"
        assert 'category_name' in df.columns, "category_name column is missing"
        assert not df['category_id'].isnull().any(), "Found null values in category_id"
        assert not df['category_name'].isnull().any(), "Found null values in category_name"
        assert df['category_id'].is_unique, "Duplicate category IDs found"
        
        print(f"Validation successful. Found {len(df)} category records.")
    except Exception as e:
        print(f"Error validating categories: {str(e)}")
        raise

def validate_customers():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'customers.csv')
        
        assert not df.empty, "Customers data is empty"
        assert 'customer_id' in df.columns, "customer_id column is missing"
        assert 'first_name' in df.columns, "first_name column is missing"
        assert 'last_name' in df.columns, "last_name column is missing"
        assert 'email' in df.columns, "email column is missing"
        assert not df['customer_id'].isnull().any(), "Found null values in customer_id"
        assert not df['first_name'].isnull().any(), "Found null values in first_name"
        assert not df['last_name'].isnull().any(), "Found null values in last_name"
        assert not df['email'].isnull().any(), "Found null values in email"
        assert df['customer_id'].is_unique, "Duplicate customer IDs found"
        assert df['email'].str.contains('@').all(), "Invalid email format found"
        
        print(f"Validation successful. Found {len(df)} customer records.")
    except Exception as e:
        print(f"Error validating customers: {str(e)}")
        raise

def validate_orders():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'orders.csv')
        
        assert not df.empty, "Orders data is empty"
        assert 'order_id' in df.columns, "order_id column is missing"
        assert 'customer_id' in df.columns, "customer_id column is missing"
        assert 'order_status' in df.columns, "order_status column is missing"
        assert 'order_date' in df.columns, "order_date column is missing"
        assert not df['order_id'].isnull().any(), "Found null values in order_id"
        assert not df['customer_id'].isnull().any(), "Found null values in customer_id"
        assert not df['order_status'].isnull().any(), "Found null values in order_status"
        assert not df['order_date'].isnull().any(), "Found null values in order_date"
        assert df['order_id'].is_unique, "Duplicate order IDs found"
        
        print(f"Validation successful. Found {len(df)} order records.")
    except Exception as e:
        print(f"Error validating orders: {str(e)}")
        raise

def validate_order_items():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'order_items.csv')
        
        assert not df.empty, "Order items data is empty"
        assert 'order_id' in df.columns, "order_id column is missing"
        assert 'item_id' in df.columns, "item_id column is missing"
        assert 'product_id' in df.columns, "product_id column is missing"
        assert 'quantity' in df.columns, "quantity column is missing"
        assert 'list_price' in df.columns, "list_price column is missing"
        assert 'discount' in df.columns, "discount column is missing"
        assert not df['order_id'].isnull().any(), "Found null values in order_id"
        assert not df['item_id'].isnull().any(), "Found null values in item_id"
        assert not df['product_id'].isnull().any(), "Found null values in product_id"
        assert not df['quantity'].isnull().any(), "Found null values in quantity"
        assert not df['list_price'].isnull().any(), "Found null values in list_price"
        assert not df['discount'].isnull().any(), "Found null values in discount"
        assert (df['quantity'] > 0).all(), "Found invalid quantity values"
        assert (df['list_price'] >= 0).all(), "Found negative list prices"
        assert ((df['discount'] >= 0) & (df['discount'] <= 1)).all(), "Found invalid discount values"
        
        print(f"Validation successful. Found {len(df)} order item records.")
    except Exception as e:
        print(f"Error validating order items: {str(e)}")
        raise

def validate_products():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'products.csv')
        
        assert not df.empty, "Products data is empty"
        assert 'product_id' in df.columns, "product_id column is missing"
        assert 'product_name' in df.columns, "product_name column is missing"
        assert 'brand_id' in df.columns, "brand_id column is missing"
        assert 'category_id' in df.columns, "category_id column is missing"
        assert not df['product_id'].isnull().any(), "Found null values in product_id"
        assert not df['product_name'].isnull().any(), "Found null values in product_name"
        assert not df['brand_id'].isnull().any(), "Found null values in brand_id"
        assert not df['category_id'].isnull().any(), "Found null values in category_id"
        assert df['product_id'].is_unique, "Duplicate product IDs found"
        
        print(f"Validation successful. Found {len(df)} product records.")
    except Exception as e:
        print(f"Error validating products: {str(e)}")
        raise

def validate_staffs():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'staffs.csv')
        
        assert not df.empty, "Staffs data is empty"
        assert 'staff_id' in df.columns, "staff_id column is missing"
        assert 'first_name' in df.columns, "first_name column is missing"
        assert 'last_name' in df.columns, "last_name column is missing"
        assert 'email' in df.columns, "email column is missing"
        assert not df['staff_id'].isnull().any(), "Found null values in staff_id"
        assert not df['first_name'].isnull().any(), "Found null values in first_name"
        assert not df['last_name'].isnull().any(), "Found null values in last_name"
        assert not df['email'].isnull().any(), "Found null values in email"
        assert df['staff_id'].is_unique, "Duplicate staff IDs found"
        assert df['email'].str.contains('@').all(), "Invalid email format found"
        
        print(f"Validation successful. Found {len(df)} staff records.")
    except Exception as e:
        print(f"Error validating staffs: {str(e)}")
        raise

def validate_stocks():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'stocks.csv')
        
        assert not df.empty, "Stocks data is empty"
        assert 'store_id' in df.columns, "store_id column is missing"
        assert 'product_id' in df.columns, "product_id column is missing"
        assert 'quantity' in df.columns, "quantity column is missing"
        assert not df['store_id'].isnull().any(), "Found null values in store_id"
        assert not df['product_id'].isnull().any(), "Found null values in product_id"
        assert not df['quantity'].isnull().any(), "Found null values in quantity"
        assert (df['quantity'] >= 0).all(), "Found negative quantity values"
        
        print(f"Validation successful. Found {len(df)} stock records.")
    except Exception as e:
        print(f"Error validating stocks: {str(e)}")
        raise

def validate_stores():
    try:
        df = read_csv_from_s3(S3_BUCKET, 'stores.csv')
        
        assert not df.empty, "Stores data is empty"
        assert 'store_id' in df.columns, "store_id column is missing"
        assert 'store_name' in df.columns, "store_name column is missing"
        assert not df['store_id'].isnull().any(), "Found null values in store_id"
        assert not df['store_name'].isnull().any(), "Found null values in store_name"
        assert df['store_id'].is_unique, "Duplicate store IDs found"
        
        print(f"Validation successful. Found {len(df)} store records.")
    except Exception as e:
        print(f"Error validating stores: {str(e)}")
        raise

with DAG(
    'validate_all_tables',
    default_args=default_args,
    description='Validates all CSV files in the data directory',
    schedule_interval='0 13 * * 3',  # Run at 1 PM every Wednesday
    catchup=False
) as dag:

    # Create tasks for each validation function
    brands_task = PythonOperator(
        task_id='brands',
        python_callable=validate_brands,
    )

    categories_task = PythonOperator(
        task_id='categories',
        python_callable=validate_categories,
    )

    customers_task = PythonOperator(
        task_id='customers',
        python_callable=validate_customers,
    )

    orders_task = PythonOperator(
        task_id='orders',
        python_callable=validate_orders,
    )

    order_items_task = PythonOperator(
        task_id='order_items',
        python_callable=validate_order_items,
    )

    products_task = PythonOperator(
        task_id='products',
        python_callable=validate_products,
    )

    staffs_task = PythonOperator(
        task_id='staffs',
        python_callable=validate_staffs,
    )

    stocks_task = PythonOperator(
        task_id='stocks',
        python_callable=validate_stocks,
    )

    stores_task = PythonOperator(
        task_id='stores',
        python_callable=validate_stores,
    )

    # Set up dependencies based on relationships between tables
    [brands_task, categories_task] >> products_task
    customers_task >> orders_task
    [products_task, orders_task] >> order_items_task
    stores_task >> stocks_task
    products_task >> stocks_task
    stores_task >> staffs_task

    # Add category sales analysis task
    category_sales_task = PythonOperator(
        task_id='category_sales_analysis',
        python_callable=analyze_category_sales,
    )

    # Set up dependencies for category sales analysis
    [categories_task, products_task, order_items_task] >> category_sales_task


    # Add product sales analysis task
    product_sales_task = PythonOperator(
        task_id='product_sales_analysis',
        python_callable=analyze_product_sales,
    )

    # Set up dependencies for product sales analysis
    [products_task, order_items_task] >> product_sales_task

    # Add product stocks analysis task
    product_stocks_task = PythonOperator(
        task_id='product_stocks_analysis',
        python_callable=analyze_product_stocks,
    )

    # Set up dependencies for product stocks analysis
    [products_task, stocks_task] >> product_stocks_task

    # Add category stocks analysis task
    category_stocks_task = PythonOperator(
        task_id='category_stocks_analysis',
        python_callable=analyze_category_stocks,
    )

    # Set up dependencies for category stocks analysis
    [categories_task, products_task, stocks_task] >> category_stocks_task
