from bottle import request, response, template
from six.moves.urllib.parse import quote
import os
import pprint

from webrecorder.basecontroller import BaseController, wr_api_spec
from webrecorder.webreccork import ValidationException

from webrecorder.models.base import DupeNameException
from webrecorder.models.datshare import DatShare
from webrecorder.utils import get_bool


# ============================================================================
class CollsController(BaseController):
    def __init__(self, *args, **kwargs):
        super(CollsController, self).__init__(*args, **kwargs)
        config = kwargs['config']

        self.allow_external = get_bool(os.environ.get('ALLOW_EXTERNAL', False))

    def init_routes(self):
        wr_api_spec.set_curr_tag('Collections')

        @self.app.post('/api/v1/collections')
        @self.api(query=['user'],
                  req=['title', 'url', 'public', 'public_index'],
                  resp='collection')

        def create_collection():
            user = self.get_user(api=True, redir_check=False)

            data = request.json or {}
            print(data)
            title = data.get('title', '')

            #if not title:
            #    title._raise_error(400, 'please enter a title to record')

            url = data.get('url', '')

            #if not url:
            #    self._raise_error(400, 'please enter a URL to record')

            coll_name = self.sanitize_title(title)

            if not coll_name:
                self._raise_error(400, 'invalid_coll_name')

            doi = data.get('doi', '') # TODO: generate doi here
            #
            #TODO: add redis object, key: jahr.monat, value: counter

            is_public = data.get('public', False)

            is_public_index = data.get('public_index', False)

            is_external = data.get('external', False)

            is_anon = self.access.is_anon(user)

            creatorList = data.get('creatorList', '')

            subjectHeaderList = data.get('subjectHeaderList', '')

            personHeaderList = data.get('personHeaderList', '')

            publisher = data.get('publisher', '')

            #if not publisher:
            #    self._raise_error(400, 'please enter the publisher of the resource')

            personHeadingText = data.get('personHeadingText', '')

            collTitle = data.get('collTitle', '')

            #if not collTitle:
            #    self._raise_error(400, 'please enter the authership information of the resource')

            noteToDachs = data.get('noteToDachs', '')

            publisherOriginal = data.get('publisherOriginal', '')

            pubTitleOriginal = data.get('pubTitleOriginal', '')

            collYear = data.get('collYear', '')

            copTitle = data.get('copTitle', '')

            subjectHeadingText = data.get('subjectHeadingText', '')

            surName = data.get('surName', '')

            persName = data.get('persName', '')

            usermail = data.get('usermail', '')

            #if not usermail:
            #    self._raise_error(400, 'invalid email adress')

            selectedGroupName = data.get('selectedGroupName', '')

            projektcode = data.get('projektcode', '') # TODO: validate projektcode

            publishYear = data.get('publishYear', '')

            listID = data.get('listID', 0)

            ticketState = data.get('ticketState')

            isCollLoaded = data.get('isCollLoaded', True)

            recordingUrl = data.get('recordingUrl', '')

            recordingTimestamp = data.get('recordingTimestamp', '')


            if is_external:
                if not self.allow_external:
                    self._raise_error(403, 'external_not_allowed')

                #if not is_anon:
                #    self._raise_error(400, 'not_valid_for_external')

            elif is_anon:
                if coll_name != 'temp':
                    self._raise_error(400, 'invalid_temp_coll_name')

            if user.has_collection(coll_name):
                self._raise_error(400, 'duplicate_name')

            try:
                collection = user.create_collection(coll_name, title=title, url=url, creatorList=creatorList, noteToDachs=noteToDachs, subjectHeaderList=subjectHeaderList,
                                                    personHeaderList=personHeaderList, publisher=publisher, collTitle=collTitle, publisherOriginal=publisherOriginal,
                                                    pubTitleOriginal=pubTitleOriginal, personHeadingText=personHeadingText, collYear=collYear, copTitle=copTitle, subjectHeadingText=subjectHeadingText,
                                                    surName=surName, persName=persName, usermail=usermail, selectedGroupName=selectedGroupName, projektcode=projektcode, publishYear=publishYear,
                                                    listID=listID, desc='', public=is_public, public_index=is_public_index, ticketState=ticketState, isCollLoaded=isCollLoaded,
                                                    recordingUrl=recordingUrl, recordingTimestamp=recordingTimestamp, doi=doi)

                if is_external:
                    collection.set_external(True)

                user.mark_updated()

                self.flash_message('Created collection <b>{0}</b>!'.format(collection.get_prop('title')), 'success')
                resp = {'collection': collection.serialize()}

            except DupeNameException as de:
                self._raise_error(400, 'duplicate_name')

            except Exception as ve:
                print(ve)
                self.flash_message(str(ve))
                self._raise_error(400, 'duplicate_name')
            print(resp)
            return resp


        @self.app.get('/api/v1/collections')
        @self.api(query=['user', 'include_recordings', 'include_lists', 'include_pages'],
                  resp='collections')
        def get_collections():
            user = self.get_user(api=True, redir_check=False)
            kwargs = {'include_recordings': get_bool(request.query.get('include_recordings')),
                      'include_lists': get_bool(request.query.get('include_lists')),
                      'include_pages': get_bool(request.query.get('include_pages')),
                     }

            collections = user.get_collections()

            return {'collections': [coll.serialize(**kwargs) for coll in collections]}

        @self.app.get('/api/v1/collection/<coll_name>')
        @self.api(query=['user'],
                  resp='collection')
        def get_collection(coll_name):
            user = self.get_user(api=True, redir_check=False)

            return self.get_collection_info(coll_name, user=user)

        @self.app.delete('/api/v1/collection/<coll_name>')
        @self.api(query=['user'],
                  resp='deleted')
        def delete_collection(coll_name):
            user, collection = self.load_user_coll(coll_name=coll_name)

            errs = user.remove_collection(collection, delete=True)
            if errs.get('error'):
                return self._raise_error(400, errs['error'])
            else:
                return {'deleted_id': coll_name}

        @self.app.put('/api/v1/collection/<coll_name>/warc')
        def add_external_warc(coll_name):
            if not self.allow_external:
                self._raise_error(403, 'external_not_allowed')

            user, collection = self.load_user_coll(coll_name=coll_name)

            self.access.assert_can_admin_coll(collection)

            if not collection.is_external():
                self._raise_error(400, 'external_only')

            num_added = collection.add_warcs(request.json.get('warcs', {}))

            return {'success': num_added}

        @self.app.put('/api/v1/collection/<coll_name>/cdx')
        def add_external_cdxj(coll_name):
            if not self.allow_external:
                self._raise_error(403, 'external_not_allowed')

            user, collection = self.load_user_coll(coll_name=coll_name)

            self.access.assert_can_admin_coll(collection)

            if not collection.is_external():
                self._raise_error(400, 'external_only')

            num_added = collection.add_cdxj(request.body.read())

            return {'success': num_added}

        @self.app.post('/api/v1/collection/<coll_name>')
        @self.api(query=['user'],
                  req=['title'],
                  resp='collection')
        def update_collection(coll_name):
            user, collection = self.load_user_coll(coll_name=coll_name)

            self.access.assert_can_admin_coll(collection)

            data = request.json or {}

            ticketStateChanged = False

            if 'title' in data:
                new_coll_title = data['title']
                new_coll_name = self.sanitize_title(new_coll_title)

                if not new_coll_name:
                    self._raise_error(400, 'invalid_coll_name')

                try:
                    new_coll_name = user.colls.rename(collection, new_coll_name, allow_dupe=False)
                except DupeNameException as de:
                    self._raise_error(400, 'duplicate_name')

                collection['title'] = new_coll_title

            if 'creatorList' in data:
                collection['creatorList'] = data['creatorList']

            if 'doi' in data:
                collection['doi'] = data['doi']

            if 'subjectHeaderList' in data:
                collection['subjectHeaderList'] = data['subjectHeaderList']

            if 'personHeaderList' in data:
                collection['personHeaderList'] = data['personHeaderList']

            if 'publisherOriginal' in data:
                collection['publisherOriginal'] = data['publisherOriginal']

            if 'publisher' in data:
                collection['publisher'] = data['publisher']

            if 'collTitle' in data:
                collection['collTitle'] = data['collTitle']

            if 'collYear' in data:
                collection['collYear'] = data['collYear']

            if 'copTitle' in data:
                collection['copTitle'] = data['copTitle']

            if 'noteToDachs' in data:
                collection['noteToDachs'] = data['noteToDachs']

            if 'surName' in data:
                collection['surName'] = data['surName']

            if 'persName' in data:
                collection['persName'] = data['persName']


            if 'personHeadingText' in data:
                collection['personHeadingText'] = data['personHeadingText']

            if 'pubTitleOriginal' in data:
                collection['pubTitleOriginal'] = data['pubTitleOriginal']

            if 'subjectHeadingText' in data:
                collection['subjectHeadingText'] = data['subjectHeadingText']

            if 'usermail' in data:
                collection['usermail'] = data['usermail']

            if 'selectedGroupName' in data:
                collection['selectedGroupName'] = data['selectedGroupName']

            if 'projektcode' in data:
                collection['projektcode'] = data['projektcode']

            if 'publishYear' in data:
                collection['publishYear'] = data['publishYear']

            if 'listID' in data:
                collection['listID'] = data['listID']

            if 'isCollLoaded' in data:
                collection.set_bool_prop('isCollLoaded', data['isCollLoaded'])

            if 'recordingUrl' in data:
                collection['recordingUrl'] = data['recordingUrl']


            if 'recordingTimestamp' in data:
                collection['recordingTimestamp'] = data['recordingTimestamp']

            if 'desc' in data:
                collection['desc'] = data['desc']

            if 'ticketState' in data:
                if collection['ticketState'] != data['ticketState']:
                    prevState = collection['ticketState']
                    newState = data['ticketState']
                    ticketStateChanged = True
                    print("Ticket State changed from {} to {}".format(prevState, newState))
                collection['ticketState'] = data['ticketState']
            if 'url' in data:
                collection['url'] = data['url']

            if ticketStateChanged:
                if data['ticketState'] == 'pending':
                    print(os.environ.get('REVIEWER_EMAIL'))
                    reviewerMailText = template(
                        'webrecorder/templates/pending_mail.html',
                        coll_name=coll_name
                    )
                    mailer = self.cork.Mailer(sender=collection['usermail'],smtp_url='starttls://eray.alpdogan@zo.uni-heidelberg.de:@mail.urz.uni-heidelberg.de:587')
                    print(user.email_addr)
                    mailer.send_email(email_addr='eray.alpdogan@zo.uni-heidelberg.de', subject='You have mail', email_text='Your email text')
                    reviewerMailTitle = 'Webrecorder: New collection awaiting review!'
                    reviewerMail = os.environ.get('REVIEWER_EMAIL')
                    self.cork.mailer.send_email(reviewerMail, reviewerMailTitle, reviewerMailText)
                elif data['ticketState'] == 'complete':
                    print('sending complete mail')
                    completeMailText = template(
                        'webrecorder/templates/complete_mail.html',
                        coll_name=coll_name
                    )
                    completeMailTitle = 'Webrecorder: Your collection has been reviewed!'
                    self.cork.mailer.send_email(collection['usermail'] + ', ' + user.email_addr, completeMailTitle, completeMailText)

                # TODO: create landing page on approve: call download, create template


            # TODO: notify the user if this is a request from the admin panel
            if 'public' in data:
                #if self.access.is_superuser() and data.get('notify'):
                #    pass
                collection.set_public(data['public'])

            if 'public_index' in data:
                collection.set_bool_prop('public_index', data['public_index'])

            collection.mark_updated()
            return {'collection': collection.serialize()}

        @self.app.get('/api/v1/collection/<coll_name>/page_bookmarks')
        @self.api(query=['user'],
                  resp='bookmarks')
        def get_page_bookmarks(coll_name):
            user, collection = self.load_user_coll(coll_name=coll_name)

            rec = request.query.get('rec')
            if rec:
                recording = collection.get_recording(rec)
                if not recording:
                    return {'page_bookmarks': {}}

                rec_pages = collection.list_rec_pages(recording)
            else:
                rec_pages = None

            return {'page_bookmarks': collection.get_all_page_bookmarks(rec_pages)}

        # DAT
        @self.app.post('/api/v1/collection/<coll_name>/dat/share')
        def dat_do_share(coll_name):
            user, collection = self.load_user_coll(coll_name=coll_name)
            print(user)
            # BETA only
            self.require_admin_beta_access(collection)

            try:
                data = request.json or {}
                print(data)
                result = DatShare.dat_share.share(collection, data.get('always_update', False))
            except Exception as e:
                result = {'error': 'api_error', 'details': str(e)}

            if 'error' in result:
                self._raise_error(400, result['error'])

            return result

        @self.app.post('/api/v1/collection/<coll_name>/dat/unshare')
        def dat_do_unshare(coll_name):
            user, collection = self.load_user_coll(coll_name=coll_name)

            # BETA only
            self.require_admin_beta_access(collection)

            try:
                result = DatShare.dat_share.unshare(collection)
            except Exception as e:
                result = {'error': 'api_error', 'details': str(e)}

            if 'error' in result:
                self._raise_error(400, result['error'])

            return result


        @self.app.post('/api/v1/collection/<coll_name>/sendmeta')
        @self.api(query=['user'],
                  resp='reviewed')
        def send_meta(coll_name):
            user, collection = self.load_user_coll(coll_name=coll_name)
            # Serializing json
            json_object = json.dumps(collection, indent = 4)
            print(json_object)
            # Writing to sample.json
            with open("sample.json", "w") as outfile:
                outfile.write(json_object)

        @self.app.post('/api/v1/collection/<coll_name>/commit')
        def commit_file(coll_name):
            user, collection = self.load_user_coll(coll_name=coll_name)

            self.access.assert_can_admin_coll(collection)

            data = request.json or {}

            res = collection.commit_all(data.get('commit_id'))
            if not res:
                return {'success': True}
            else:
                return {'commit_id': res}

        # LEGACY ENDPOINTS (to remove)
        # Collection view (all recordings)
        @self.app.get(['/<user>/<coll_name>', '/<user>/<coll_name>/'])
        @self.jinja2_view('collection_info.html')
        def coll_info(user, coll_name):
            return self.get_collection_info_for_view(user, coll_name)

        @self.app.get(['/<user>/<coll_name>/<rec_list:re:([\w,-]+)>', '/<user>/<coll_name>/<rec_list:re:([\w,-]+)>/'])
        @self.jinja2_view('collection_info.html')
        def coll_info(user, coll_name, rec_list):
            #rec_list = [self.sanitize_title(title) for title in rec_list.split(',')]
            return self.get_collection_info_for_view(user, coll_name)

        wr_api_spec.set_curr_tag(None)

    def get_collection_info_for_view(self, user, coll_name):
        self.redir_host()

        result = self.get_collection_info(coll_name, user=user, include_pages=True)

        result['coll'] = result['collection']['id']
        result['coll_name'] = result['coll']
        result['coll_title'] = quote(result['collection']['title'])

        #if not result or result.get('error'):
        #    self._raise_error(404, 'Collection not found')

        return result

    def get_collection_info(self, coll_name, user=None, include_pages=False):
        user, collection = self.load_user_coll(user=user, coll_name=coll_name)

        result = {'collection': collection.serialize(include_rec_pages=include_pages,
                                                     include_lists=True,
                                                     include_recordings=True,
                                                     include_pages=True,
                                                     check_slug=coll_name)}

        result['user'] = user.my_id
        result['size_remaining'] = user.get_size_remaining()

        return result
