# Register this blueprint by adding the following line of code 
# to your entry point file.  
# app.register_functions(<function name>) 

import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

import azure.functions as func
import logging

function_httptrig_readBlobContainer = func.Blueprint()

@function_httptrig_readBlobContainer.route(route='readBlobContainer')
def readBlobContainer(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function httptrig_readBlobContainer processed a request.')

    storageAccUrl = os.environ['AZURE_STORAGE_ACCOUNT_CONNECTION']
    logging.info(f'storageAccUrl= {storageAccUrl}')

    credential = DefaultAzureCredential()

    blobServiceClient = BlobServiceClient.from_connection_string(storageAccUrl, credential)

    responseBody = ''
    separator = '\n'

    ## Get list of storage containers
    containersIterator = blobServiceClient.list_containers()
    containers = list(containersIterator)

    ## As the Iterator already hit the end, this list is created empty.
    ## And the map and join are not executed and myString is empty
    myList = list(containersIterator)
    myString = separator.join(map(lambda x: x.name, myList))

    ## As the list is empty, the map is not executed even once
    ## and because of that, there is no error (like name property not found or similar)
    ## and the resulting string is empty
    myList2 = list()
    myString = separator.join(map(lambda x: x.name, myList2))

    responseBody += '[List of containers]' + separator
    responseBody += separator.join(map(lambda x: x.name, containers))
    responseBody += separator + separator

    ## This would send the output to the Debug Console in VS Code
    ## for container in containers:
    ##    print("\t" + container.name)

    ## Get list of Blobs per container
    for container in containers:
        containerClient = blobServiceClient.get_container_client(container.name)
        
        blobsIterator = containerClient.list_blobs()
        blobs = list(blobsIterator)
        
        responseBody += f'[Blobs in container: {container.name}]' + separator
        responseBody += separator.join(map(lambda x: f'{x.name} [{x.last_modified}]', blobs))
        responseBody += separator + separator

    return func.HttpResponse(responseBody)
