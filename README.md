# APLICAÇÃO PARA O VACATION #
  This API is built using FastAPI. 
  It is integrated and comunicates directly with Aurora.
  The objective of this application is to ease the work of the sellers from vacation club for easy data transfer, maintainability and reminder of new costumers.

## Index ##
  - [Installation] (#installation)
  - [Documentation] (#documentation)
  - [Configuration] (#configuration)
  - [Structure] (#structure)

## Instalation ##
  1. This application is built to be run on docker, it contains 2 files Dockerfile and docker-compose.yml for an easy setup.

## Documentation ##
### Users ###
  The users module is built for user iterations which includes the basics of any CRUD application, login and password recovery operations.
  #### Create new user ####
  - **Description**: 
    A new user can only be created by someone with access to the platform. 
    This requires the existing user to authenticate and create the new user. 
    Each parameter from the user is validated (e.g., username uniqueness) and sensitive data like passwords are hashed.
    Associated entities like companies, permissions, and contacts can be linked during creation.
    Input is sanitized by framework mechanisms to prevent common injection attacks.
  - **API Version**: V1
  - **Method**: POST
  - **Endpoint**: `/users`
  - **Headers**:
    - **Authorization**: "Bearer <access_token>"
  - **Request**:
    ```JSON
      {
        "first_name": "string",
        "last_name": "string",
        "full_name": "string",
        "username": "string", // Must be unique
        "password": "string",
        "department_id": integer, 
        "company_id": integer,
        "local_id": integer,
        "companies": [
          integer,
          ...
        ],
        "permissions": [
          integer,
          ...
        ],
        "contacts": [
          {
            "contact": "string",
            "contact_type_id": integer,
            "name": "string", // Optional: description/name for the contact
            "main_contact": boolean,
            "public": boolean
          },
          ...
        ]
      }
    ```
    
  #### Fetch Users ####
    - **Description**:
      Retrieves a paginated list of active (not deleted) users. This endpoint supports flexible searching, filtering, and ordering.
        - *General Search*: A broad, case-insensitive search (search parameter) can be performed across the user's first name, last name, full name, and employee number using OR logic.
        - *Specific Filtering*: Precise, case-insensitive filtering (and_filters parameter) can be applied to specific fields using AND logic (all specified conditions must be met). Allowed fields for filtering include: id, first_name, last_name, full_name, employee_num, username, email, department_id, company_id, local_id, department__name, company__name, local__name.
        - *Ordering*: Results can be ordered by various fields (order_by parameter). Prefix the field name with a hyphen (-) for descending order. Allowed fields for ordering include: id, first_name, last_name, full_name, employee_num, created_at, updated_at, last_time_seen, department__name, company__name, local__name.
        - *Pagination*: Results are paginated. The response includes links (next_page, previous_page) to navigate through pages, preserving any applied search, filter, and ordering parameters.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/users`
    - **Parameters**:
      - `page` (integer, optional, default: 1): The page number to retrieve (must be >= 1).
      - `page_size` (integer, optional, default: 10): The number of users to return per page (must be >= 1 and <= 100).
      - `search` (string, optional): A general search term applied across default fields (first_name, last_name, full_name, employee_num) with OR logic.
      - `and_filters` (JSONString, optional): Specific filters applied with AND logic. Pass as query parameters like {"field_name": "value"}. Example: ?and_filters{"department__name":"DTI", "local_id": 5}. Uses case-insensitive matching. See allowed fields in the description.
      - `order_by` (string, optional): Field name to sort results by. Prefix with - for descending order (e.g., -last_name). See allowed fields in the description.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
  
  #### Fetch user details ####
    - **Description**:
      Fetches detailed information for a specific employee identified by their id.
      The response includes personal information (first_name, last_name, full_name, username, employee_num, extra_info), timestamps (created_at, updated_at, deactivated_at, last_time_seen), associated primary entities (department, company, local), lists of associated entities (companies, permissions), and all associated contacts. 
      It raises a 404 error if no employee with the given id is found.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/users/details/{id}`
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
  
  #### Update user details ####
    - **Description**:
      Updates the details for a specific employee identified by id. 
      This endpoint allows modification of core employee fields (first_name, last_name, full_name, username, password, employee_num, extra_info, department_id, company_id, local_id), associated contacts, companies, and permissions.
      It validates the uniqueness of the username if provided.
      Password updates require sending the new plain text password, which will be securely hashed.
      The deactivate field can be used to set or clear the deactivated_at timestamp.
      Only the fields intended for modification need to be sent in the request body. All changes are logged.
    - **API Version**: V1
    - **Method**: PUT
    - **Endpoint**: `/users/details/{id}`
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
    - **Request**:
      ```JSON
        {
          "first_name": "string", // Optional
          "last_name": "string", // Optional
          "full_name": "string", // Optional
          "username": "string", // Optional
          "password": "string", // Optional
          "employee_num": "string", // Optional
          "extra_info": "string", // Optional
          "department_id": "integer", // Optional
          "company_id": "integer", // Optional
          "local_id": "integer", // Optional
          "deactivate": "boolean", // Optional
          "companies": [
            "integer", // company_id
            ... 
          ],
          "permissions": [
            "integer",  // permission_id
            ...
          ],
          "contacts": [
            {
              "contact_type_id": "integer", // Required if updating contacts
              "contact": "string", // Required if updating contacts
              "name": "string", // Optional
              "main_contact": "boolean", //Optional, default: false
              "public": "boolean", // Optional, default: true
            }
          ]
        }
      ```
  #### Delete user ####
    - **Description**:
      Performs a soft delete on the employee identified by the provided id.
      This is achieved by setting the deleted_at timestamp field in the database to the current time.
      The endpoint first verifies if the user exists; if not found, it returns a 404 error.
    - **API Version**: V1
    - **Method**: DELETE
    - **Endpoint**: `/users/details/{id}`
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
  
  #### /me ####
    - **Description**:
      This function validates the access token provided by the client to identify and retrieve the details of the currently authenticated user. 
      If the token is valid and belongs to an active user, it returns the user's detailed information; otherwise, it raises appropriate errors (401 for invalid/expired tokens, 500 for internal issues).
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/users/me`
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"

  #### Login ####
    - **Description**:
      Authenticates a user based on their username and password.
      It verifies the credentials against active, non-deleted employee records.
      Upon successful authentication, it generates and returns both an access token (valid for 30 minutes) and a refresh token (valid for 5 days).
      If the username is not found or the password does not match, a 401 Unauthorized error is returned.
    - **API Version**: V1
    - **Method**: POST
    - **Endpoint**: `/users/authenticate`
    - **Request**:
      ```JSON
        {
          "username": "string",
          "password": "string"
        }
      ```
  
  #### Password recovery request ####
    - **Description**:
      This process allows a user to initiate a password reset via their registered email address.
      If the requested email is valid or exists on the database, it will be sent an email to the owner of the email with a code to authorize the password recovery.
      This code is only valid for 15 minutes.
      *IMPORTANT!* This request will return the user details, which will be required to proceed with the password recovery.
    - **API Version**: V1
    - **Method**: POST
    - **Endpoint**: `/users/recovery-request`
    - **Request**:
      ```JSON
        {
          "email":"user@example.com"
        }
      ```
  
  #### Code verification ####
    - **Description**:
      This endpoint verifies the password recovery code sent to the user's email.
      It takes the user's id and the code they entered.
      The endpoint checks if a valid, non-expired recovery token exists for the user, decrypts it, and compares the stored secret code with the provided code.
      It manages a limited number of attempts (initially 5).
      If the code is incorrect, the attempt counter is decremented.
      If the code expires or the maximum attempts are reached, the recovery token is invalidated.
      On successful verification, it returns the user's detailed information.
    - **API Version**: V1
    - **Method**: POST
    - **Endpoint**: `/users/verify-code`
    - **Request**:
      ```JSON
        {
          "code": "string",
          "id": 0
        }
      ```
  
  #### Password recovery ####
    - **Description**:
      This endpoint finalizes the password recovery process by setting a new password for the user.
      This endpoint requires the user's id, the verification code received via email, and the desired new_password.
      It first verifies the provided id and code using the same logic as the /users/verify-code endpoint (checking for existence, validity, expiration, and attempts).
      If the verification is successful, the new password is securely hashed and updated in the user's record.
      The recovery token used for this process is then invalidated to prevent reuse.
    - **API Version**: V1
    - **Method**: PUT
    - **Endpoint**: `/users/password-recovery`
    - **Request**:
      ```JSON
        {
          "code": "string",
          "id": 0,
          "password": "string"
        }
      ```
  #### Fetch employees by permission ####
    - **Description**:
      Retrieves a list of active employees who possess a specific permission, identified by the permission_id.
      This endpoint filters out employees who are deactivated or deleted.
      For each matching employee, it returns their basic details (id, first_name, last_name, full_name), their primary department, company, local, and a list of their associated public contacts.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/users/permission/{permission_id}`
  #### Refresh access token ####
    - **Description**:
      Generates a new access token using a valid refresh token. 
      The refresh token must be provided in the X-Refresh-Token header.
      The endpoint first validates the refresh token (checking signature, expiration, and associated user status).
      If valid, it issues a new access token with a standard expiration time (30 minutes).
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/users/refresh-token`
    - **Headers**:
      - **X-Refresh-Token**: "string"

    

### Languages ###
  The Languages module is built for language manipulations which includes the basics of CRUD, Create, Read, Update e Delete


