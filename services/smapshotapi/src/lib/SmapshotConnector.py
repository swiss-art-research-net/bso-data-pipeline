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

    def _listPhotographers(self, limit, offset=0, additionalParams={}):
        url = self._apiPath("/photographers")
        params = {}
        headers = {'Authorization': 'Bearer %s' % self.TOKEN, 'accept': 'application/json', 'Content-Type': 'application/json'}
        for key in additionalParams:
            params[key] = additionalParams[key]
        try:
            r = requests.get(url=url, params=params, headers=headers)
        except:
            return False
        return r.json()

    def addImage(self, *, title, collection_id=36, photographer_ids=[0], iiif_url, width, height, original_id, latitude, longitude, license, name=None, regionByPx, date_orig, date_shot_min, date_shot_max, is_published=True, view_type="terrestrial", correction_enabled=False, observation_enabled=True, framing_mode="single_image"):
        """
        Adds a new IIIF image to sMapshot
        :param title: The title of the image
        :type title: str
        :param collection_id: The id of the collection the image should be added to (default: 36)
        :type collection_id: int
        :param photographer_ids: The ids of the photographers of the image (default: [0])
        :type photographer_ids: list
        :param iiif_url: The IIIF Image API URL of the image
        :type iiif_url: str
        :param width: The width of the image
        :type width: int
        :param height: The height of the image
        :type height: int
        :param original_id: The original id of the image
        :type original_id: str
        :param latitude: The latitude of the initial location for the image
        :type latitude: float
        :param longitude: The longitude of the initial location for the image
        :type longitude: float
        :param license: The license or owner of the image
        :type license: str
        :param name: The name of the image (deprecated)
        :type name: str
        :param regionByPx: The region of the image in pixels (x,y,width,height)
        :type regionByPx: list
        :param date_orig: The date of the image as recorded
        :type date_orig: str
        :param date_shot_min: The earliest date for the image
        :type date_shot_min: str
        :param date_shot_max: The latest date for the image
        :type date_shot_max: str
        :param is_published: Whether the image should be published (default: True)
        :type is_published: bool
        :param view_type: The type of view the image is (default: "terrestrial")
        :type view_type: str
        :param correction_enabled: Whether the image metadata can be corrected on sMapshot (default: False)
        :type correction_enabled: bool
        :param observation_enabled: Whether observations (annotations) should be enabled for the image (default: True)
        :type observation_enabled: bool
        :param framing_mode: The framing mode of the image. "single_image" or "composite_image" (default: "single_image")
        :type framing_mode: str

        """
        attributes = {
            "iiif_data" : {
                "image_service3_url": iiif_url,
                "regionByPx": regionByPx
            },
            "is_published": is_published,
            "original_id": original_id,
            "title": title,
            "collection_id": collection_id,
            "license": license,
            "observation_enabled": observation_enabled,
            "correction_enabled": correction_enabled,
            "view_type": view_type,
            "height": height,
            "width": width,
            "date_orig": date_orig,
            "apriori_location": {
                "longitude": longitude,
                "latitude": latitude
            },
            "photographer_ids": photographer_ids,
            "framing_mode": framing_mode
        }
        if name:
            attributes["name"] = name
        if date_shot_min and date_shot_max:
            attributes["date_shot_min"] = date_shot_min
            attributes["date_shot_max"] = date_shot_max
        elif date_shot_min:
            attributes["date_shot"] = date_shot_min
        elif date_shot_max:
            attributes["date_shot"] = date_shot_max
        url = self._apiPath("/images")
        headers = {'Authorization': 'Bearer %s' % self.TOKEN, 'accept': 'application/json', 'Content-Type': 'application/json'}
        r = requests.post(url=url, headers=headers, data=json.dumps(attributes))
        return r.json()
        
    def addPhotographer(self, *, firstname='', lastname, company='', link):
        """
        Adds a new photographer to the sMapshot collection
        :param firstname: The firstname of the photographer
        :type firstname: str
        :param lastname: The lastname of the photographer
        :type lastname: str
        :param company: The company the entry belongs to
        :type company: str
        :param link: The URI of the photographer
        """
        attributes = {
            "first_name": firstname,
            "last_name": lastname,
            "link": link,
            "company": company
        }
        url = self._apiPath("/photographers")
        headers = {'Authorization': 'Bearer %s' % self.TOKEN, 'accept': 'application/json', 'Content-Type': 'application/json'}
        r = requests.post(url=url, headers=headers, data=json.dumps(attributes))
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

    def listPhotographers(self, additionalParams= {}):
        """
        Retrieves the photographers for a given collection owner. 
        Additional parameters for the API call can be passed as a dictionary.
        :param additionalParams: Additional parameters for the API call
        :type additionalParams: dict
        """
        offset = 0

        return self._listPhotographers(999999, 0, additionalParams)

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

    def setImagePhotographerIDs(self, imageId, photographerIDs):
        """
        Set photographer ids for a given image id
        :param imageId: The image id
        :type imageId: int
        :param photographerIDs: The photographer ids to set
        :type photographerIDs: list
        """
        attributes = {
            "photographer_ids": photographerIDs
        }
        return self.setImageAttributes(int(imageId), attributes)

    def setImagePublishedState(self, imageId, published, newSate):
        """
        Set attributes for a given image id
        :param imageId: The image id
        :type imageId: int
        :param published: Whether the image should be published
        :type published: bool
        :param newState: The new state of the image
        :type newState: str
        """
        url = self._apiPath("/images/%d/state" % imageId)
        headers = {'Authorization': 'Bearer %s' % self.TOKEN, 'accept': 'application/json', 'Content-Type': 'application/json'}
        data = {
            "publish": published,
            "new_state": newSate
        }
        r = requests.put(url=url, headers=headers, data=json.dumps(data))
        return r.json()

    def setImageRegion(self, imageId, iiifUrl, region):
        """
        Set the region and IIIF URL for a given image id
        :param imageId: The image id
        :type imageId: int
        :param iiifUrl: The IIIF URL
        :type iiifUrl: str
        :param region: The region
        :type region: list
        """
        attributes = {
            "iiif_data" : {
                "image_service3_url": iiifUrl,
                "regionByPx": region
            }
        }
        return self.setImageAttributes(int(imageId), attributes)