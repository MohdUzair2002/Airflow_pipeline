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

def write_csv_to_s3(df, bucket, key):
    """Write DataFrame to CSV in S3 bucket."""
    try:
        # Convert DataFrame to CSV string
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_buffer.getvalue()
        )
    except Exception as e:
        print(f'Error writing {key} to S3: {str(e)}')
        raise

def validate_brands():
    """Validate and clean brands data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'brands.csv')
        print(df)
        # Clean brand names
        df['brand_name'] = df['brand_name'].str.strip().str.title()
        
        # Check for missing values in required fields
        required_fields = ['brand_id', 'brand_name']
        if df[required_fields].isnull().any().any():
            raise ValueError('Missing values in required brand fields')
        
        # Check for unique brand IDs
        if len(df['brand_id'].unique()) != len(df):
            raise ValueError('Duplicate brand IDs found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'brands.csv')
        print('Brands validation and cleaning successful')
    except Exception as e:
        print(f'Brands validation failed: {str(e)}')
        raise

def validate_categories():
    """Validate and clean categories data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'categories.csv')
        # Clean category names
        df['category_name'] = df['category_name'].str.strip().str.title()
        
        # Check for missing values in required fields
        required_fields = ['category_id', 'category_name']
        if df[required_fields].isnull().any().any():
            raise ValueError('Missing values in required category fields')
            
        # Check for unique category IDs
        if len(df['category_id'].unique()) != len(df):
            raise ValueError('Duplicate category IDs found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'categories.csv')
        print('Categories validation and cleaning successful')
    except Exception as e:
        print(f'Categories validation failed: {str(e)}')
        raise

def validate_staffs():
    """Validate and clean staffs data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'staffs.csv')
        # Clean name fields
        df['first_name'] = df['first_name'].str.strip().str.title()
        df['last_name'] = df['last_name'].str.strip().str.title()
        df['email'] = df['email'].str.strip().str.lower()
        
        # Check for missing values in required fields
        required_fields = ['staff_id', 'first_name', 'last_name', 'email']
        if df[required_fields].isnull().any().any():
            raise ValueError('Missing values in required staff fields')
            
        # Check for unique staff IDs
        if len(df['staff_id'].unique()) != len(df):
            raise ValueError('Duplicate staff IDs found')
            
        # Check for unique email addresses
        if len(df['email'].unique()) != len(df):
            raise ValueError('Duplicate email addresses found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'staffs.csv')
        print('Staffs validation and cleaning successful')
    except Exception as e:
        print(f'Staffs validation failed: {str(e)}')
        raise

def validate_customers():
    """Validate and clean customers data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'customers.csv')
        # Clean name and contact fields
        df['first_name'] = df['first_name'].str.strip().str.title()
        df['last_name'] = df['last_name'].str.strip().str.title()
        df['email'] = df['email'].str.strip().str.lower()
        # df['phone'] = df['phone'].str.strip()
        
        # Check for missing values
        if df.isnull().any().any():
            raise ValueError('Found missing values in customers data')
            
        # Check for unique customer IDs
        if len(df['customer_id'].unique()) != len(df):
            raise ValueError('Duplicate customer IDs found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'customers.csv')
        print('Customers validation and cleaning successful')
    except Exception as e:
        print(f'Customers validation failed: {str(e)}')
        raise

def validate_orders():
    """Validate orders data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'orders.csv')
        # Clean and standardize date fields
        date_fields = ['order_date', 'required_date', 'shipped_date']
        for field in date_fields:
            df[field] = pd.to_datetime(df[field], errors='coerce')
        
        # Clean order status - convert to string first
        df['order_status'] = df['order_status'].astype(str).str.strip().str.upper()
        
        # Check for missing values in required fields
        required_fields = ['order_id', 'customer_id', 'order_status']
        if df[required_fields].isnull().any().any():
            raise ValueError('Missing values in required order fields')
        # Check for unique order IDs
        if len(df['order_id'].unique()) != len(df):
            raise ValueError('Duplicate order IDs found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'orders.csv')
        print('Orders validation and cleaning successful')
    except Exception as e:
        print(f'Orders validation failed: {str(e)}')
        raise

def validate_order_items():
    """Validate order items data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'order_items.csv')
        # Clean numeric fields
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['list_price'] = pd.to_numeric(df['list_price'], errors='coerce')
        df['discount'] = pd.to_numeric(df['discount'], errors='coerce').clip(0, 1)
        
        # Check for missing values in required fields
        required_fields = ['order_id', 'item_id', 'product_id', 'quantity']
        if df[required_fields].isnull().any().any():
            raise ValueError('Missing values in required order items fields')
        # Validate numeric fields
        if (df['quantity'] <= 0).any():
            raise ValueError('Invalid quantity values found')
        if (df['list_price'] <= 0).any():
            raise ValueError('Invalid price values found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'order_items.csv')
        print('Order items validation and cleaning successful')
    except Exception as e:
        print(f'Order items validation failed: {str(e)}')
        raise

def validate_products():
    """Validate products data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'products.csv')
        # Clean product names
        df['product_name'] = df['product_name'].str.strip().str.title()
        
        # Clean numeric fields
        df['list_price'] = pd.to_numeric(df['list_price'], errors='coerce')
        df['model_year'] = pd.to_numeric(df['model_year'], errors='coerce')
        
        # Check for missing values in required fields
        required_fields = ['product_id', 'product_name', 'list_price']
        if df[required_fields].isnull().any().any():
            raise ValueError('Missing values in required product fields')
        # Check for unique product IDs
        if len(df['product_id'].unique()) != len(df):
            raise ValueError('Duplicate product IDs found')
        # Validate price values
        if (df['list_price'] <= 0).any():
            raise ValueError('Invalid price values found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'products.csv')
        print('Products validation and cleaning successful')
    except Exception as e:
        print(f'Products validation failed: {str(e)}')
        raise

def validate_stocks():
    """Validate stocks data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'stocks.csv')
        # Clean numeric fields
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        
        # Check for missing values
        if df.isnull().any().any():
            raise ValueError('Found missing values in stocks data')
        # Validate quantity values
        if (df['quantity'] < 0).any():
            raise ValueError('Negative stock quantities found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'stocks.csv')
        print('Stocks validation and cleaning successful')
    except Exception as e:
        print(f'Stocks validation failed: {str(e)}')
        raise

def validate_stores():
    """Validate stores data for completeness and consistency."""
    try:
        df = read_csv_from_s3(S3_BUCKET, 'stores.csv')
        # Clean store information
        df['store_name'] = df['store_name'].str.strip().str.title()
        df['phone'] = df['phone'].str.strip()
        df['email'] = df['email'].str.strip().str.lower()
        df['street'] = df['street'].str.strip().str.title()
        df['city'] = df['city'].str.strip().str.title()
        df['state'] = df['state'].str.strip().str.upper()
        # Convert zip_code to string and clean it
        df['zip_code'] = df['zip_code'].astype(str).str.strip()
        
        # Check for missing values in required fields
        required_fields = ['store_id', 'store_name']
        if df[required_fields].isnull().any().any():
            raise ValueError('Missing values in required store fields')
        # Check for unique store IDs
        if len(df['store_id'].unique()) != len(df):
            raise ValueError('Duplicate store IDs found')
            
        # Save cleaned data
        write_csv_to_s3(df, S3_BUCKET, 'stores.csv')
        print('Stores validation and cleaning successful')
    except Exception as e:
        print(f'Stores validation failed: {str(e)}')
        raise