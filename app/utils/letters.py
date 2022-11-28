from flask import url_for
from notifications_utils.formatters import unescaped_formatted_list
from notifications_utils.postal_address import PostalAddress

LETTER_VALIDATION_MESSAGES = {
    'letter-not-a4-portrait-oriented': {
        'title': 'Your letter is not A4 portrait size',
        'detail': (
            'You need to change the size or orientation of {invalid_pages}. <br>'
            'Files must meet our '
            '<a class="govuk-link govuk-link--destructive" href="{letter_spec_guidance}" target="_blank">'
            'letter specification'
            '</a>.'
        ),
        'summary': (
            'Validation failed because {invalid_pages} {invalid_pages_are_or_is} not A4 portrait size.<br>'
            'Files must meet our '
            '<a class="govuk-link govuk-link--no-visited-state" href="{letter_spec_guidance}">'
            'letter specification'
            '</a>.'
        ),
    },
    'content-outside-printable-area': {
        'title': 'Your content is outside the printable area',
        'detail': (
            'You need to edit {invalid_pages}.<br>'
            'Files must meet our '
            '<a class="govuk-link govuk-link--destructive" href="{letter_spec_guidance}">'
            'letter specification'
            '</a>.'
        ),
        'summary': (
            'Validation failed because content is outside the printable area on {invalid_pages}.<br>'
            'Files must meet our '
            '<a class="govuk-link govuk-link--no-visited-state" href="{letter_spec_guidance}" target="_blank">'
            'letter specification'
            '</a>.'
        ),
    },
    'letter-too-long': {
        'title': 'Your letter is too long',
        'detail': (
            'Letters must be 10 pages or less (5 double-sided sheets of paper). <br>'
            'Your letter is {page_count} pages long.'
        ),
        'summary': (
            'Validation failed because this letter is {page_count} pages long.<br>'
            'Letters must be 10 pages or less (5 double-sided sheets of paper).'
        ),
    },
    'no-encoded-string': {
        'title': 'Sanitise failed - No encoded string'
    },
    'unable-to-read-the-file': {
        'title': 'There’s a problem with your file',
        'detail': (
            'Notify cannot read this PDF.'
            '<br>Save a new copy of your file and try again.'
        ),
        'summary': (
            'Validation failed because Notify cannot read this PDF.<br>'
            'Save a new copy of your file and try again.'
        ),
    },
    'address-is-empty': {
        'title': 'The address block is empty',
        'detail': (
            'You need to add a recipient address.<br>'
            'Files must meet our '
            '<a class="govuk-link govuk-link--destructive" href="{letter_spec_guidance}" target="_blank">'
            'letter specification'
            '</a>.'
        ),
        'summary': (
            'Validation failed because the address block is empty.<br>'
            'Files must meet our '
            '<a class="govuk-link govuk-link--no-visited-state" href="{letter_spec_guidance}" target="_blank">'
            'letter specification'
            '</a>.'
        ),
    },
    'not-a-real-uk-postcode': {
        'title': 'There’s a problem with the address for this letter',
        'detail': (
            'The last line of the address must be a real UK postcode.'
        ),
        'summary': (
            'Validation failed because the last line of the address is not a real UK postcode.'
        ),
    },
    'cant-send-international-letters': {
        'title': 'There’s a problem with the address for this letter',
        'detail': (
            'You do not have permission to send letters to other countries.'
        ),
        'summary': (
            'Validation failed because your service cannot send letters to other countries.'
        ),
    },
    'not-a-real-uk-postcode-or-country': {
        'title': 'There’s a problem with the address for this letter',
        'detail': (
            'The last line of the address must be a UK postcode or '
            'another country.'
        ),
        'summary': (
            'Validation failed because the last line of the address is '
            'not a UK postcode or another country.'
        ),
    },
    'not-enough-address-lines': {
        'title': 'There’s a problem with the address for this letter',
        'detail': (
            f'The address must be at least {PostalAddress.MIN_LINES} '
            f'lines long.'
        ),
        'summary': (
            f'Validation failed because the address must be at least '
            f'{PostalAddress.MIN_LINES} lines long.'
        ),
    },
    'too-many-address-lines': {
        'title': 'There’s a problem with the address for this letter',
        'detail': (
            f'The address must be no more than {PostalAddress.MAX_LINES} '
            f'lines long.'
        ),
        'summary': (
            f'Validation failed because the address must be no more '
            f'than {PostalAddress.MAX_LINES} lines long.'
        ),
    },
    'invalid-char-in-address': {
        'title': 'There’s a problem with the address for this letter',
        'detail': (
            "Address lines must not start with any of the following characters: @ ( ) = [ ] ” \\ / , < > ~"
        ),
        'summary': (
            "Validation failed because address lines must not start with any of the "
            "following characters: @ ( ) = [ ] ” \\ / , < > ~"
        ),
    },
    'notify-tag-found-in-content': {
        'title': 'There’s a problem with your letter',
        'detail': (
            'Your file includes a letter you’ve downloaded from Notify.<br>'
            'You need to edit {invalid_pages}.'
        ),
        'summary': (
            'Validation failed because your file includes a letter '
            'you’ve downloaded from Notify on {invalid_pages}.'
        )
    },
}


def get_letter_validation_error(validation_message, invalid_pages=None, page_count=None):
    if not invalid_pages:
        invalid_pages = []
    if validation_message not in LETTER_VALIDATION_MESSAGES:
        return {'title': 'Validation failed'}

    invalid_pages_are_or_is = 'is' if len(invalid_pages) == 1 else 'are'

    invalid_pages = unescaped_formatted_list(
        invalid_pages,
        before_each='',
        after_each='',
        prefix='page',
        prefix_plural='pages'
    )

    return {
        'title': LETTER_VALIDATION_MESSAGES[validation_message]['title'],
        'detail': LETTER_VALIDATION_MESSAGES[validation_message]['detail'].format(
            invalid_pages=invalid_pages,
            invalid_pages_are_or_is=invalid_pages_are_or_is,
            page_count=page_count,
            letter_spec_guidance=url_for('.letter_specification')
        ),
        'summary': LETTER_VALIDATION_MESSAGES[validation_message]['summary'].format(
            invalid_pages=invalid_pages,
            invalid_pages_are_or_is=invalid_pages_are_or_is,
            page_count=page_count,
            letter_spec_guidance=url_for('.letter_specification'),
        ),
    }
