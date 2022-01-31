import json
import requests

class SmapshotConnector:
    
    API_URL = ""
    OWNER_ID = False
    TOKEN = False
    
    LIMIT = 20
    
        
    """
    Class encapsulating the sMapshot API
    :param owner: The owner id of the sMapshot collection
    :type owner: int
    :param url: The URL of the sMapshot API. Defaults to https://smapshot.heig-vd.ch/api/v1
    :type url: str
    :param token: The token to use for authentication. If not set, only public data is accessible
    """

    def __init__(self, owner = 3, url = "https://smapshot.heig-vd.ch/api/v1", token = False):
        self.API_URL = url
        self.OWNER_ID = owner
        self.TOKEN = token
        
    def _apiPath(self, path):
        return self.API_URL + path

    def _listImages(self, limit, offset=0, additionalParams={}):
        url = self._apiPath("/images")
        params = {
            'owner_id': self.OWNER_ID, 
            'limit': limit, 
            'offset': offset
        }
        for key in additionalParams:
            params[key] = additionalParams[key]
        try:
            r = requests.get(url=url, params=params)
        except:
            return False
        return r.json()
    
    def _listObservations(self, limit, offset=0, additionalParams={}):
        url = self._apiPath("/observations")
        params = {
            'owner_id': self.OWNER_ID, 
            'limit': limit, 
            'offset': offset
        }
        for key in additionalParams:
            params[key] = additionalParams[key]
        try:
            r = requests.get(url=url, params=params)
        except:
            return False
        return r.json()
        
    def getImageAttributes(self, imageId):
        """
        Retrieves additional attributes for a given image id
        :param imageId: The image id
        :type imageId: int
        """
        url = self._apiPath("/images/%d/attributes" % imageId)
        r = requests.get(url=url)
        return r.json()

    def listImages(self,additionalParams = {}):
        """
        Retrieves the images for a given collection owner. Defaults to collection owner 3 (SARI). 
        Additional parameters for the API call can be passed as a dictionary.
        :param additionalParams: Additional parameters for the API call
        :type additionalParams: dict
        """
        offset = 0

        initialImages = self._listImages(1, 0, additionalParams)
        numberOfImages = initialImages['count']
        
        images = []
        
        while offset < numberOfImages:
            images += self._listImages(self.LIMIT, offset, additionalParams)['rows']
            offset += self.LIMIT
            
        return images

    def listObservations(self,additionalParams = {}):
        """
        Retrieves the observations for a given collection owner. 
        Additional parameters for the API call can be passed as a dictionary.
        :param additionalParams: Additional parameters for the API call
        :type additionalParams: dict
        """
        offset = 0

        return self._listObservations(999999, 0, additionalParams)

    def listValidatedObservations(self, validatedAfterDate=False):
        """
        Retrieves the validated observations for a given collection owner. 
        To retrieve only observations validated after a given data, pass the date in the validatedAfterDate parameter.
        :param validatedAfterDate: Retrieve only observations that have been validated after this date
        :type validatedAfterDate: str
        """
        additionalParams = {}
        if validatedAfterDate:
            additionalParams['date_validated_min'] = str(validatedAfterDate)
        return self.listObservations(additionalParams)
        
    def listValidatedImages(self, validatedAfterDate=False):
        """
        Retrieves the valitated images for a given collection owner. Defaults to collection owner 3 (SARI)
        To retrieve only images validated after a given data, pass the date in the validatedAfterDate parameter.
        :param validatedAfterDate: Retrieve only images that have been validated after this date
        :type validatedAfterDate: str
        """
        additionalParams = {'state[0]': 'validated'}
        if validatedAfterDate:
            additionalParams['date_validated_min'] = str(validatedAfterDate)
        return self.listImages(additionalParams)


    def setImageAttributes(self, imageId, attributes):
        """
        Set attributes for a given image id
        :param imageId: The image id
        :type imageId: int
        :param attributes: The attributes to set
        :type attributes: dict
        """
        url = self._apiPath("/images/%d/attributes" % imageId)
        headers = {'Authorization': 'Bearer %s' % self.TOKEN, 'accept': 'application/json', 'Content-Type': 'application/json'}
        r = requests.put(url=url, headers=headers, data=json.dumps(attributes))
        return r.json()

    def setImageRegion(self, imageId, iiifUrl, region):
        attributes = {
            "iiif_data" : {
                "image_service3_url": iiifUrl,
                "regionByPx": region
            }
        }
        return self.setImageAttributes(int(imageId), attributes)