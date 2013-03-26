import re
import string
import gdata.contacts.client
import gdata.contacts.data
import atom.data
import gdata.data

class TIM():
    """This class modify the contact phone number to add the tim prefix"""
    def __init__(self, email, password):
        """
        Constructor for the ContactsSample object.
        
        Takes an email and password corresponding to a gmail account to
        access the functionality of the Contacts feed.
        
        Args:
          email: [string] The e-mail address of the account to use for the sample.
          password: [string] The password corresponding to the account specified by
              the email parameter.
        """
        # Login to the gdata api
        self.gd_client = gdata.contacts.client.ContactsClient(source='TIM-Contacts')
        self.gd_client.ClientLogin(email, password, self.gd_client.source)

        # Create an update feed.
        self.update_feed = gdata.contacts.data.ContactsFeed()


        # This sohuld change so that we provide the operator and default area code via variable

  
        self.phone_patterns = [
        # USED EXCLUSEVLY FOR SP MOBILE NUMBERS
        # This will have to change once more sates use 9 digit numbers
        # NNNNN-NNNN -> 041 11 NNNNN-NNNN
        ('^(?P<numero>\d{9})$', '04111\g<numero>'),
        # Assigne operator code plus default area code 21 to br numbers that have no area code
        # NNNN-NNNN -> 041 21 NNNN-NNNN
        ('^(?P<numero>\d{8})$', '04121\g<numero>'),
        # Adds operator code 21 to any number withought it
        # 0AA NNNN(N)?-NNNN -> 041 AA NNNN(N)?-NNNN
        # AA NNNN(N)?-NNNN -> 041 AA NNNN(N)?-NNNN
        ('^0?(?P<area>\d{2})(?P<numero>\d{8,9})$', '041\g<area>\g<numero>'),
        # Changes any BR number from international format to national format with operator code
        # 0055 AA NNNN(N)?-NNNN -> 041 AA NNNN(N)?-NNNN
        # +55 AA NNNN(N)?-NNNN -> 041 AA NNNN(N)?-NNNN
        ('^(00|\+)55(?P<area>\d{2})(?P<numero>\d{8,9})$', '041\g<area>\g<numero>'),
        # Adds operator code to any international number
        # 00CC N* -> +41CC N*
        # +CC N* -> +41CC N*
        ('^(00|\+)(?!55)(?P<ddi>\d+)$', '+41\g<ddi>')
        ]
        

    def update_contacts(self):
        '''
        This Method fetches up to 3000 contacts and then passes the address_book to the self.__modify_number() method.
        self.__modify_number() yields one modifyed contact at a time back to update_contacts.
        update_contats makes sure we are creating a feed that is not bigger then 100 entry and then flushes it to the server.
        '''
        # Ftech address book with up to 300 contacts
        query = gdata.contacts.client.ContactsQuery()    
        query.max_results = '3000'
        address_book = self.gd_client.GetContacts(q = query)

        # Displays how many contats were fetched
        print("Fetched %s contacts"%(len(address_book.entry)))

        for contact in self.__modify_contacts(address_book):
            # Add contact to update feed
            self.__add_to_feed(contact)
        # Flush any remaining contact
        if len(self.update_feed.entry):
            self.__flush_feed(self.update_feed)

    def __add_to_feed(self, contact):
        '''
        This method should be used to manage the feed size,
        and make sure we flush all changes when it reaches 100 entry.
        '''
        if len(self.update_feed.entry) < 100:
            self.update_feed.AddUpdate(entry=contact, batch_id_string='update')
        else:
            self.__flush_feed(self.update_feed)
            self.update_feed.AddUpdate(entry=contact, batch_id_string='update')

    def __flush_feed(self, feed):
        '''
        This method receives a prepopulated feed and flushes it to the server
    
        Args:
            feed: The feed to be pushed to the server
        Yields:
            N/A

        To-Do: 
            Still need to make sure every entry was correctly updated
        '''
        # Debuging message
        print("Flushing %s contacts to server" %(len(feed.entry)))
     
        # submit the batch request to the server.
        response_feed = self.gd_client.ExecuteBatch(feed, 'https://www.google.com/m8/feeds/contacts/default/full/batch')
        # Create a new feed. CLear all entry that have just beig flushed
        self.update_feed = gdata.contacts.data.ContactsFeed()

        # Debuging Message
        # for entry in response_feed.entry:
            # print '%s: %s (%s)' % (entry.batch_id.text, entry.batch_status.code, entry.batch_status.reason)

    def __modify_number(self, phone):
        '''
        This method modify a phone number to make sure that all Brazilian numbers are formated as:
        041 AA NNNNNNNN (8 digits numbers) or 041 11 NNNNNNNNN(9 digit saopaulo modile numbers).
        Where 41 is the operator code. For now only TIM is supported

        Args:
            phone: [string] The phone number to be modified
        Yields:
            phone: The modifyed phone number
        '''
        # Remove any non numeric caracter from phone number
        # Maybe I can do that with a regex
        if phone[0] == '+':
            phone = '+' + re.sub('[^\d]', '', phone)

        else:
            phone = re.sub('[^\d]', '', phone)

        # Apply the changes to this phone number
        for (pattern, replace) in self.phone_patterns:
            phone = re.sub(pattern, replace, phone)   

        return phone

    def __modify_contacts(self, address_book):

        for contact in address_book.entry:
            
            # Only modify Contacts that have phone
            if contact.phone_number:
                # Modifying Contact phone number
                # print("Modifying Contact: %s" %(contact.name.full_name.text))
                for i, phone in enumerate(contact.phone_number):
                    contact.phone_number[i].text = self.__modify_number(phone.text)
                # Mark contact as modified
                contact_modified = True

            # Plase holder to make other modifications
            elif False:
                pass
                # contact_modified = True

            # If contact was not modifed we should not return it
            else:
                contact_modified = False
            
            # Only return contacts that were modified
            if contact_modified:
                yield contact

def main():
    user = 'user_name@dgmail.com'
    password = 'password'
    frederic = TIM(user, password)
    print('Loging in as: %s' %(user))
    frederic.update_contacts()


if __name__ == '__main__':
    main()