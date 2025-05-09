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

### Companies ###
  #### Fetch companies ####
  - **Description**:
    Retrieves a list of all **active** companies. Each company in the list will include its associated **locals**.
    Companies are considered active if their `deactivated_at` field is `null`.
    The list is ordered by company name.
  - **API Version**: V1
  - **Method**: GET
  - **Endpoint**: `/companies`
  - **Headers**:
    - **Authorization**: "Bearer <access_token>"
  - **Success Response (200 OK)**:
    ```JSON
    [
      {
        "id": "integer",
        "name": "string",
        "acronym": "string",
        // ... other company fields ...
        "locals": [
          {
            "id": "integer",
            "name": "string",
            "short": "string",
            "background": "string", // e.g., "#FFFFFF"
            "text": "string" // e.g., "#000000"
          },
          // ... more locals for this company ...
        ]
      },
      // ... more company objects ...
    ]
    ```
  - **Error Responses**:
    - `500 Internal Server Error`: If an unexpected error occurs during data retrieval.
  #### Create company ####
    - **Description**:
      Creates a new company. This endpoint allows for the simultaneous creation of associated locals and the establishment of links to existing ticket categories.
      The operation is performed within a database transaction to ensure data integrity.
      - *Validation*: Input data is validated. For example, the company name must be unique.
      - *Locals*: If a list of local data is provided, new local records will be created and associated with the new company.
      - *Ticket Categories*: If a list of existing ticket category IDs is provided, associations will be created between the new company and these categories.
    - **API Version**: V1
    - **Method**: POST
    - **Endpoint**: `/companies`
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
      - **Permission**: `tecnico`
    - **Request**:
      ```JSON
        {
          "name": "string", // Required, must be unique
          "acronym": "string", // Required
          "locals": [ // Optional
            {
              "name": "string", // Required if locals ispresent
              "short": "string", // Required if locals is present
              "background": "string", // Required if locals is present (e.g., "#FFFFFF")
              "text": "string" // Required if locals is present (e.g., "#000000")
            },
            ...
          ],
          "ticket_category_ids": [ // Optional: List of existing TicketCategory ids
            "integer",
            ...
          ]
        }
      ```
    - **Success Response (201 Created)**: Returns the newly created company object (details may vary based on serialization, but typically includes ID, name, acronym, and potentially the newly created/associated relations if fetched post-creation).
    - **Error Responses**:
      - `400 Bad Request`: If required fields are missing or data is invalid.
      - `409 Conflict`: If a company with the same name already exists, or other integrity constraint violations.
      - `500 Internal Server Error`: If an unexpected error occurs during creation.
  #### Fetch company by ID ####
    - **Description**:
      Retrieves detailed information for a specific company identified by its `company_id`.
      The response includes the company's core details, a list of its associated `locals`, and a list of its `ticket_category_associations`.
      This endpoint is useful for getting a complete view of a single company.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/companies/details/{company_id}`
    - **Parameters**:
      - `company_id` (integer, required): The unique ID of the company to retrieve.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
      - **Permission**: `tecnico`
    - **Success Response (200 OK)**:
      ```JSON
      {
        "id": "integer",
        "name": "string",
        "acronym": "string",
        "deactivated_at": "string or null (datetime)",
        // ... other direct company fields ...
        "locals": [
          {
            "id": "integer",
            "name": "string",
            "short": "string",
            "background": "string",
            "text": "string"
          },
          // ... more locals ...
        ],
        "ticket_categories": [ 
          "integer", // id of the TicketCategory
          // ... more associated ticket categories ...
        ]
      }
      ```
    - **Error Responses**:
      - `404 Not Found`: If no company with the specified `company_id` exists.
      - `500 Internal Server Error`: If an unexpected error occurs during data retrieval.
  #### Update company details ####
    - **Description**:
      Updates the details of an existing company identified by its `company_id`.
      This endpoint allows for modification of the company's direct attributes (`name`, `acronym`),
      as well as comprehensive management of its associated `locals` and `ticket_category` associations.
      All database operations are performed within a transaction to ensure atomicity.
      - **Direct Attributes**: `name` and `acronym` can be updated. If provided, they cannot be empty.
      - **Locals Management**:
        - If the `locals` array is provided, it will synchronize the company's locals with the provided list.
        - Locals in the list with an `id` will be updated with the provided data.
        - Locals in the list without an `id` will be created as new locals associated with the company.
        - Any existing locals associated with the company that are *not* present in the provided `locals` list (identified by their `id`) will be deleted.
      - **Ticket Category Associations**:
        - If the `ticket_category_ids` array is provided, it will synchronize the company's associations with ticket categories.
        - Associations will be created for any `ticket_category_ids` in the list that are not already linked to the company.
        - Existing associations will be removed if their `ticket_category_id` is not present in the provided list.
    - **API Version**: V1
    - **Method**: PUT
    - **Endpoint**: `/companies/details/{company_id}`
    - **Parameters**:
      - `company_id` (integer, required): The unique ID of the company to update.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
      - **Permission**: `tecnico`
    - **Request Body**:
      ```JSON
      {
        "name": "string", // Optional, cannot be empty if provided
        "acronym": "string", // Optional, cannot be empty if provided
        "locals": [ // Optional: Full list to synchronize locals
          {
            "id": "integer", // Optional: Include to update an existing local
            "name": "string", // Required for new locals, cannot be empty if provided for update
            "short": "string", // Required for new locals, cannot be empty if provided for update
            "background": "string", // Required for new locals, cannot be empty if provided for update
            "text": "string" // Required for new locals, cannot be empty if provided for update
          },
          // ... more local objects ...
        ],
        "ticket_category_ids": [ // Full list of ticket category ids to associate
          "integer",
          // ... more ticket category IDs ...
        ]
      }
      ```
    - **Success Response (200 OK)**: Returns the updated company object, including its `locals` and `ticket_categories` (as a list of category IDs, based on current `to_dict_details` in `Companies` model).
    - **Error Responses**:
      - `400 Bad Request`: If input data is invalid (e.g., empty name/acronym when provided, invalid local structure).
      - `404 Not Found`: If the company with the specified `company_id` does not exist.
      - `409 Conflict`: If updating the company name results in a duplicate name, or other integrity constraint violations.
      - `500 Internal Server Error`: If an unexpected error occurs during the update process.
  #### Deactivate company ####
    - **Description**:
      Deactivates a company by setting its `deactivated_at` timestamp to the current UTC date and time.
      This is a "soft delete" operation, meaning the company record remains in the database but is marked as inactive.
      If the company is already deactivated, the operation is considered successful and no changes are made.
    - **API Version**: V1
    - **Method**: DELETE
    - **Endpoint**: `/companies/details/{company_id}`
    - **Parameters**:
      - `company_id` (integer, required): The unique ID of the company to deactivate.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
      - **Permission**: `tecnico`
    - **Success Response (204 No Content)**: Indicates successful deactivation (or that the company was already deactivated). No content is returned in the body.
    - **Error Responses**:
      - `404 Not Found`: If no company with the specified `company_id` exists.
      - `500 Internal Server Error`: If an unexpected error occurs during the deactivation process.

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
  #### Ticket presets ####
    - **Description**:
      Retrieves a list of all defined ticket presets along with the count of tickets matching each preset's filter criteria.
      This endpoint allows for optional base filtering (`and_filters`) to be applied *before* applying the specific filters defined within each preset.
      - **Base Filtering (`and_filters`)**: If provided, these filters (using the same format as the `fetch_tickets` endpoint's `and_filters`) are applied to the initial ticket query. This narrows down the pool of tickets before preset filters are considered.
      - **Preset Filtering**: For each preset retrieved from the database, if it has a `filter` defined (as a valid JSON string representing filter conditions), these filters are applied to the (potentially pre-filtered) ticket set.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/tickets/presets`
    - **Parameters**:
      - `and_filters` (JSONString, optional): Specific base filters applied with AND logic before preset filters. Pass as a JSON string in query parameters, similar to the `fetch_tickets` endpoint. Example: `?and_filters={"company_id": 10}`
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
    - **Response**:
      ```JSON
      [
        { "name": "novos", "filter": "{\"status_id\": 1}", "count": 15 },...
      ]
      ```
  #### Ticket logs ####
    - **Description**:
      Retrieves the logs for a specific ticket identified by its UID.
      This endpoint fetches all log entries associated with the ticket, ordering them by creation date in descending order (most recent first).
      Each log entry includes details about the change made, the user who made the change, and the timestamp of the change.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/tickets/details/{uid}/logs`
    - **Path Parameters**:
      - `uid` (string, required): The unique identifier of the ticket to retrieve logs for.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
      - **Permission**: `tecnico`
### Ticket Categories ###
  #### Create ticket category ####
  - **Description**:
    Creates a new ticket category.
    This endpoint allows the creation of a new ticket category with a unique name.
    It validates that the provided name is unique within the system.
    Upon successful creation, it returns the details of the newly created category.
  - **API Version**: V1
  - **Method**: POST
  - **Endpoint**: `/ticket-categories`
  - **Headers**:
    - **Authorization**: "Bearer <access_token>"
  - **Request**:
    ```JSON
    {
      "name": "string", // Required, must be unique
      "description": "string", // Optional
      "companies": [ // Optional: List of company IDs to associate with this category
        "integer", // company_id
        ...
      ]
    }
    ```
  #### Fetch ticket categories ####
    - **Description**:
      Retrieves a list of all ticket categories.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/ticket-categories`
    - **Parameters**:
      - `company_id` (integer, optional): The ID of the company to filter categories by.
  #### Fetch ticket category details ####
    - **Description**:
      Retrieves the details of a specific ticket category identified by its ID.
    - **API Version**: V1
    - **Method**: GET
    - **Endpoint**: `/ticket-categories/details/{id}`
    - **Parameters**:
      - `id` (integer, required): The ID of the ticket category to retrieve.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
  #### Update ticket category ####
    - **Description**:
      Updates the details of an existing ticket category identified by its ID.
    - **API Version**: V1
    - **Method**: PUT
    - **Endpoint**: `/ticket-categories/details/{id}`
    - **Parameters**:
      - `id` (integer, required): The ID of the ticket category to update.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"
    - **Request**:
      ```JSON
      {
        "name": "string", // Optional
        "description": "string", // Optional
        "active": true, // Optional
        "companies": [ // Optional: List of company IDs to associate. This will replace existing associations.
          "integer", // company_id
          ...
        ]
      }
      ```
  #### Delete ticket category ####
    - **Description**:
      Deletes a ticket category identified by its ID.
    - **API Version**: V1
    - **Method**: DELETE
    - **Endpoint**: `/ticket-categories/details/{id}`
    - **Parameters**:
      - `id` (integer, required): The ID of the ticket category to soft delete.
    - **Headers**:
      - **Authorization**: "Bearer <access_token>"

### Ticket Subcategories ###
  #### Delete ticket subcategories ####
  - **Description**:
    Deletes a ticket subcategory identified by its ID.  
  - **API Version**: V1
  - **Method**: DELETE
  - **Endpoint**: `/ticket-subcategories/details/{id}`
  - **Headers**:
    - **Authorization**: "Bearer <access_token>"
    - **Required Permission**: `tecnico`

### Ticket Types ###
  #### Fetch ticket types ####
  - **Description**:
    Retrieves a list of all ticket types.
  - **API Version**: V1
  - **Method**: GET
  - **Endpoint**: `/ticket-types`

### Ticket Priorities ###
  #### Fetch ticket priorities ####
  - **Description**:
    Retrieves a list of all ticket priorities.
  - **API Version**: V1
  - **Method**: GET
  - **Endpoint**: `/ticket-priorities`

### Ticket Assistance Types ###
  #### Fetch ticket assistance types ####
  - **Description**:
    Retrieves a list of all ticket assistance types.
  - **API Version**: V1
  - **Method**: GET
  - **Endpoint**: `/ticket-assistance-types`
