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

### Tickets ###
  #### Create ticket ####
  - **Description**:
    Creates a new ticket.
    This endpoint handles the ticket creation within a database transaction, ensuring atomicity.
    It automatically logs the creation action, associates any provided CC email addresses, handles optional file uploads, and sends a confirmation email to the requester (and CCs users if applicable).
    The user creating the ticket is recorded based on the provided authentication token.
    File uploads should be sent as part of a `multipart/form-data` request, alongside the JSON payload for ticket details.
  - **API Version**: V1
  - **Method**: POST
  - **Endpoint**: `/tickets`
  - **Headers**:
    - **Authorization**: "Bearer <access_token>"
    - **Content-Type**: `multipart/form-data` (Required if sending files) or `application/json` (if no files)
  - **Request Body**:
    ```JSON
    {
      "request": "string", // Required: Detailed description of the issue/request
      "requester_id": "integer", // Required: ID of the user requesting support
      "company_id": "integer", // Required: ID of the company associated with the ticket
      "category_id": "integer", // Required: ID of the ticket category
      "priority_id": "integer", // Required: ID of the ticket priority
      "type_id": "integer", // Required: ID of the ticket type
      "assistance_type_id": "integer", // Required: ID of the assistance type
      "agent_id": "integer", // Optional: ID of the agent assigned (if known at creation)
      "subcategory_id": "integer", // Optional: ID of the ticket subcategory
      "status_id": "integer", // Optional: Initial status ID (often set automatically)
      "supplier_reference": "string", // Optional: Reference from a supplier
      "equipments": "string", // Optional: JSON string containing equipment details
      "suppliers": "string", // Optional: JSON string containing supplier details
      "ccs": [ // Optional: List of user IDs to CC on the ticket
        "integer",
        ...
      ]
    }
    ```
  - **Request Body (Files part, in multipart request)**:
    - `files`: One or more files attached to the request. (Optional)  

  #### Fetch tickets ####
    - **Description**:
      Retrieves a paginated list of tickets. This endpoint provides powerful searching, filtering, and ordering capabilities.
      - **General Search (`search`)**: Performs a case-insensitive search across multiple fields using OR logic. The fields searched by default include: `id`, `uid`, `subject`, `request`, `response`, `internal_comment`, `supplier_reference`, requester's names (`first_name`, `last_name`, `full_name`), agent's names (`first_name`, `last_name`, `full_name`), `company__name`, `category__name`, and `subcategory__name`.
      - **Specific Filtering (`and_filters`)**: Applies precise filters using AND logic (all conditions must match). Filters are generally case-insensitive for strings.
        - *Allowed Fields*: `id`, `uid`, `subject`, `request`, `response`, `internal_comment`, `supplier_reference`, `spent_time`, `company_id`, `category_id`, `subcategory_id`, `status_id`, `type_id`, `priority_id`, `assistance_type_id`, `requester_id`, `agent_id`, and related fields like `company__name`, `category__name`, `status__name`, `requester__username`, `agent__email`, etc. (See `ALLOWED_AND_FILTER_FIELDS` in the code for the full list).
        - *Date Filtering*: For date fields (`prevention_date`, `created_at`, `closed_at`), use suffixes `_after` (inclusive) and `_before` (exclusive) with dates in `YYYY-MM-DD` format. Example: `?and_filters={"created_at_after": "2023-01-01", "created_at_before": "2023-12-31"}`.
        - *List Filtering*: For fields ending in `_id`, you can provide a list of IDs to match any of them. Example: `?and_filters={"status_id": [1, 2, 5]}`.
      - **Ordering (`order_by`)**: Sorts the results by a specified field. Prefix the field name with `-` for descending order (`-created_at`).
        - *Allowed Fields*: `id`, `uid`, `subject`, `created_at`, `closed_at`, various `_id` fields, and related name fields like `company__name`, `status__name`, `requester__full_name`, etc. Default order is `-created_at`.
      - **Pagination**: Results are paginated. The response includes metadata like `total_items`, `total_pages`, `current_page`, and links (`next_page`, `previous_page`) that preserve the applied filters and sorting.
      - **Prefetching**: Related data like status, priority, category, requester, agent, and attachments are prefetched for efficiency.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/tickets`
    - **Parameters**:
      - `page` (integer, optional, default: 1): The page number to retrieve (>= 1).
      - `page_size` (integer, optional, default: 10): The number of tickets per page (>= 1, <= 100).
      - `search` (string, optional): General search term applied across default fields (OR logic).
      - `and_filters` (JSONString, optional): Specific filters applied with AND logic. Pass as a JSON string in query parameters. Example: `?and_filters={"status_id": 5, "requester__full_name": "John Doe"}`
      - `order_by` (string, optional): Field to sort by (example, `priority_id`, `-created_at`). Defaults to `-created_at`.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
  #### Fetch ticket details ####
    - **Description**:
      Retrieves the detailed information for a specific ticket identified by its unique identifier (UID).
      This endpoint fetches the ticket and prefetches related data for efficiency, including: status, priority, category, subcategory, requester, agent, company, CCs, attachments, type, assistance type, and the user who created the ticket.
      It returns a comprehensive dictionary containing all relevant ticket fields and related object details.
      If no ticket is found with the provided UID, a 404 Not Found error is returned.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/tickets/details/{uid}`
    - **Path Parameters**:
      - `uid` (string, required): The unique identifier of the ticket to retrieve.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
  #### Update ticket ####
    - **Description**:
      Updates the details of an existing ticket identified by its UID.
      This endpoint allows modification of various ticket fields, managing CCs, and adding new attachments.
      Updates are performed within a database transaction to ensure atomicity.
      Key behaviors include:
        - **Automatic Status Changes**: The ticket status might automatically change (e.g., to 'Assigned') if an `agent_id` is provided for the first time.
        - **Closing Timestamp**: If the `status_id` is updated to a 'Closed' status, the `closed_at` timestamp is automatically set. If it's changed from 'Closed' to another status, `closed_at` is cleared.
        - **CCs Management**: The list of CC users can be fully replaced by providing a new list in the `ccs` field.
        - **File Uploads**: New files can be attached to the ticket using a `multipart/form-data` request.
        - **Logging**: All changes made to the ticket fields (including CCs and attachments) are logged for auditing purposes.
        - **Notifications**: Email notifications are sent to the requester if an agent is assigned, or if the status changes to 'Closed' or 'Reopened'.
      Only the fields intended for modification need to be sent in the request body.
    - **API Version**: V1
    - **Method**: PUT
    - **Endpoint**: `/tickets/{uid}`
    - **Path Parameters**:
      - `uid` (string, required): The unique identifier of the ticket to update.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
      - **Content-Type**: `multipart/form-data` (Required if sending files) or `application/json` (if no files)
    - **Request Body (JSON part, typically named 'ticket_data' in multipart request)**:
      ```JSON
      {
        "requester_id": "integer",
        "category_id": "integer",
        "type_id": "integer",
        "subcategory_id": "integer",
        "assistance_type_id": "integer",
        "response": "string",
        "internal_comment": "string",
        "suppliers": "string",
        "equipments": "string",
        "prevention_date": "string",
        "spent_time": "string",
        "status_id": "integer",
        "agent_id": "integer",
        "supplier_reference": "string",
        "ccs": ["integer", ...],  
      }
      ```
    - **Request Body (Files part, in multipart request)**:
      - `files`: One or more new files to attach to the ticket. (Optional)



