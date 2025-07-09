# Database Schema and Insert Operations Analysis

## Overview
This document analyzes the database schema for the ATM Dashboard application and compares it with the insert operations in the code, particularly focusing on the `combined_atm_retrieval_script.py` file.

## Tables Examined
1. `terminal_details`
2. `regional_atm_counts`
3. `atm_cash_info`
4. `regional_data`
5. `terminal_cash_information`

## Schema Analysis Results

### 1. `terminal_details` Table
**Schema in database:**
```
Column                    Type                 Nullable   Default
----------------------------------------------------------------------
id                        integer              NO         nextval('terminal_details_id_seq'::regclass)
unique_request_id         uuid                 NO         gen_random_uuid()
terminal_id               character varying    NO         None
location                  text                 YES        None
issue_state_name          character varying    YES        None
serial_number             character varying    YES        None
retrieved_date            timestamp with time zone NO     None
fetched_status            character varying    NO         None
raw_terminal_data         jsonb                NO         None
fault_data                jsonb                YES        None
metadata                  jsonb                YES        None
created_at                timestamp with time zone YES    CURRENT_TIMESTAMP
updated_at                timestamp with time zone YES    CURRENT_TIMESTAMP
```

**Insert Operations in Code (atm_database.py):**
```python
cursor.execute("""
    INSERT INTO terminal_details 
    (unique_request_id, terminal_id, location, issue_state_name, 
     serial_number, retrieved_date, fetched_status, raw_terminal_data, 
     fault_data, metadata) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    terminal.get('unique_request_id'),
    terminal.get('terminalId'),
    terminal.get('location'),
    terminal.get('issueStateName'),
    terminal.get('serialNumber'),
    terminal.get('retrievedDate'),
    terminal.get('fetched_status'),
    json.dumps(terminal),  # Store the complete terminal data
    json.dumps(fault_data),
    json.dumps(metadata)
))
```

**Assessment:** The insert operation in the code matches the database schema. The code doesn't explicitly set `created_at` and `updated_at` as these fields have default values.

### 2. `regional_atm_counts` Table
**Schema in database:**
```
Column                    Type                 Nullable   Default
----------------------------------------------------------------------
id                        integer              NO         nextval('regional_atm_counts_id_seq'::regclass)
unique_request_id         uuid                 NO         gen_random_uuid()
region_code               character varying    NO         None
count_available           integer              YES        0
count_warning             integer              YES        0
count_zombie              integer              YES        0
count_wounded             integer              YES        0
count_out_of_service      integer              YES        0
date_creation             timestamp with time zone YES    CURRENT_TIMESTAMP
total_atms_in_region      integer              YES        0
percentage_available      numeric              YES        0.0
percentage_warning        numeric              YES        0.0
percentage_zombie         numeric              YES        0.0
percentage_wounded        numeric              YES        0.0
percentage_out_of_service numeric              YES        0.0
```

**Insert Operations in Code (atm_database.py):**
```python
cursor.execute("""
    INSERT INTO regional_atm_counts 
    (unique_request_id, region_code, count_available, count_warning, 
     count_zombie, count_wounded, count_out_of_service, 
     date_creation, total_atms_in_region, percentage_available, 
     percentage_warning, percentage_zombie, percentage_wounded, 
     percentage_out_of_service) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    region.get('unique_request_id'),
    region.get('region_code'),
    region.get('count_available', 0),
    region.get('count_warning', 0),
    region.get('count_zombie', 0),
    region.get('count_wounded', 0),
    region.get('count_out_of_service', 0),
    region.get('date_creation'),
    region.get('total_atms_in_region', 0),
    region.get('percentage_available', 0.0),
    region.get('percentage_warning', 0.0),
    region.get('percentage_zombie', 0.0),
    region.get('percentage_wounded', 0.0),
    region.get('percentage_out_of_service', 0.0)
))
```

**Assessment:** The insert operation in the code matches the database schema. All required fields are present and types match.

### 3. `atm_cash_info` Table
**Schema in database:** Table does not exist in the current database.

**Insert Operations in Code (atm_database.py):**
```python
cursor.execute("""
    INSERT INTO atm_cash_info 
    (unique_request_id, terminal_id, business_code, technical_code, 
     external_id, retrieval_timestamp, event_date, total_cash_amount, 
     total_currency, cassettes_data, raw_cash_data) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    cash.get('unique_request_id'),
    cash.get('terminal_id'),
    cash.get('business_code'),
    cash.get('technical_code'),
    cash.get('external_id'),
    cash.get('retrieval_timestamp'),
    cash.get('event_date'),
    cash.get('total_cash_amount'),
    cash.get('total_currency'),
    json.dumps(cash.get('cassettes_data', [])),
    json.dumps(cash)  # Store complete cash data
))
```

**Assessment:** The `atm_cash_info` table doesn't exist in the database yet. The code attempts to create the table with the correct schema before inserting data, but it seems the table creation might have failed or not been executed. This should be investigated.

### 4. `regional_data` Table
**Schema in database:**
```
Column                    Type                 Nullable   Default
----------------------------------------------------------------------
id                        integer              NO         nextval('regional_data_id_seq'::regclass)
unique_request_id         uuid                 NO         gen_random_uuid()
region_code               character varying    NO         None
retrieval_timestamp       timestamp with time zone YES    CURRENT_TIMESTAMP
raw_regional_data         jsonb                NO         None
count_available           integer              YES        0
count_warning             integer              YES        0
count_zombie              integer              YES        0
count_wounded             integer              YES        0
count_out_of_service      integer              YES        0
total_atms_in_region      integer              YES        0
created_at                timestamp with time zone YES    CURRENT_TIMESTAMP
updated_at                timestamp with time zone YES    CURRENT_TIMESTAMP
```

**Insert Operations in Code (atm_database_old.py):**
```python
cursor.execute("""
    INSERT INTO regional_data (
        unique_request_id, region_code, count_available, count_warning,
        count_zombie, count_wounded, count_out_of_service,
        total_atms_in_region, retrieval_timestamp, raw_regional_data
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    record['unique_request_id'], region_code,
    record['count_available'], record['count_warning'],
    record['count_zombie'], record['count_wounded'],
    record['count_out_of_service'], record['total_atms_in_region'],
    datetime.now(self.dili_tz), json.dumps(raw_json_data)
))
```

**Assessment:** The insert operation matches the database schema for the most important columns. However, it's important to note that this insert operation is found in `atm_database_old.py`, not in the main `atm_database.py` file. This suggests that the `regional_data` table might be a newer addition or a replacement for `regional_atm_counts`. The current `combined_atm_retrieval_script.py` should be updated to use the appropriate table.

### 5. `terminal_cash_information` Table
**Schema in database:**
```
Column                    Type                 Nullable   Default
----------------------------------------------------------------------
id                        integer              NO         nextval('terminal_cash_information_id_seq'::regclass)
unique_request_id         uuid                 NO         gen_random_uuid()
terminal_id               character varying    NO         None
business_code             character varying    YES        None
technical_code            character varying    YES        None
external_id               character varying    YES        None
retrieval_timestamp       timestamp with time zone YES    CURRENT_TIMESTAMP
event_date                timestamp with time zone YES    None
total_cash_amount         numeric              YES        0.00
total_currency            character varying    YES        None
cassettes_data            jsonb                NO         None
raw_cash_data             jsonb                YES        None
cassette_count            integer              YES        0
has_low_cash_warning      boolean              YES        false
has_cash_errors           boolean              YES        false
```

**Insert Operations in Code (terminal_cash_information_retrieval.py):**
```python
cursor.execute("""
    INSERT INTO terminal_cash_information (
        unique_request_id,
        terminal_id,
        business_code,
        technical_code,
        external_id,
        retrieval_timestamp,
        event_date,
        total_cash_amount,
        total_currency,
        cassettes_data,
        raw_cash_data,
        cassette_count,
        has_low_cash_warning,
        has_cash_errors
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    record['unique_request_id'],
    record['terminal_id'],
    record['business_code'],
    record['technical_code'],
    record['external_id'],
    record['retrieval_timestamp'],
    record['event_date'],
    record['total_cash_amount'],
    record['total_currency'],
    json.dumps(record['cassettes_data']),
    json.dumps(record['raw_cash_data']),
    record['cassette_count'],
    record['has_low_cash_warning'],
    record['has_cash_errors']
))
```

**Assessment:** The insert operation in the `terminal_cash_information_retrieval.py` file matches the database schema perfectly. All fields are correctly handled.

## Recommendations

1. **Fix atm_cash_info Table**: The `atm_cash_info` table doesn't exist in the database. Update the `combined_atm_retrieval_script.py` to use the `terminal_cash_information` table instead, as it appears to be the replacement table for cash information.

2. **Update Regional Data Handling**: The code appears to be using both `regional_atm_counts` and `regional_data` tables. Determine which is the correct table to use and update the code accordingly. It seems that `regional_data` might be the newer table based on the schema.

3. **Code Consistency**: Make sure the insert operations in `combined_atm_retrieval_script.py` are consistent with the database schema. Currently, it seems to be using older table structures in some places.

4. **Error Handling**: Add better error handling for table creation to ensure all tables exist before attempting to insert data.

5. **Documentation**: Update documentation to clearly indicate which tables are current and which are deprecated.
