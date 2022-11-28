import pytest
from bs4 import BeautifulSoup
from flask import url_for

from app.utils.letters import get_letter_validation_error


@pytest.mark.parametrize('error_message, invalid_pages, expected_title, expected_content, expected_summary', [
    (
        'letter-not-a4-portrait-oriented',
        [2],
        'Your letter is not A4 portrait size',
        (
            'You need to change the size or orientation of page 2. '
            'Files must meet our letter specification.'
        ),
        (
            'Validation failed because page 2 is not A4 portrait size.'
            'Files must meet our letter specification.'
        ),
    ),
    (
        'letter-not-a4-portrait-oriented',
        [2, 3, 4],
        'Your letter is not A4 portrait size',
        (
            'You need to change the size or orientation of pages 2, 3 and 4. '
            'Files must meet our letter specification.'
        ),
        (
            'Validation failed because pages 2, 3 and 4 are not A4 portrait size.'
            'Files must meet our letter specification.'
        ),
    ),
    (
        'content-outside-printable-area',
        [2],
        'Your content is outside the printable area',
        (
            'You need to edit page 2.'
            'Files must meet our letter specification.'
        ),
        (
            'Validation failed because content is outside the printable area '
            'on page 2.'
            'Files must meet our letter specification.'
        ),
    ),
    (
        'letter-too-long',
        None,
        'Your letter is too long',
        (
            'Letters must be 10 pages or less (5 double-sided sheets of paper). '
            'Your letter is 13 pages long.'
        ),
        (
            'Validation failed because this letter is 13 pages long.'
            'Letters must be 10 pages or less (5 double-sided sheets of paper).'
        ),
    ),
    (
        'unable-to-read-the-file',
        None,
        'There’s a problem with your file',
        (
            'Notify cannot read this PDF.'
            'Save a new copy of your file and try again.'
        ),
        (
            'Validation failed because Notify cannot read this PDF.'
            'Save a new copy of your file and try again.'
        ),
    ),
    (
        'address-is-empty',
        None,
        'The address block is empty',
        (
            'You need to add a recipient address.'
            'Files must meet our letter specification.'
        ),
        (
            'Validation failed because the address block is empty.'
            'Files must meet our letter specification.'
        ),
    ),
    (
        'not-a-real-uk-postcode',
        None,
        'There’s a problem with the address for this letter',
        (
            'The last line of the address must be a real UK postcode.'
        ),
        (
            'Validation failed because the last line of the address is not a real UK postcode.'
        ),
    ),
    (
        'cant-send-international-letters',
        None,
        'There’s a problem with the address for this letter',
        (
            'You do not have permission to send letters to other countries.'
        ),
        (
            'Validation failed because your service cannot send letters to other countries.'
        ),
    ),
    (
        'not-a-real-uk-postcode-or-country',
        None,
        'There’s a problem with the address for this letter',
        (
            'The last line of the address must be a UK postcode or '
            'another country.'
        ),
        (
            'Validation failed because the last line of the address is '
            'not a UK postcode or another country.'
        ),
    ),
    (
        'not-enough-address-lines',
        None,
        'There’s a problem with the address for this letter',
        (
            'The address must be at least 3 lines long.'
        ),
        (
            'Validation failed because the address must be at least 3 lines long.'
        ),
    ),
    (
        'too-many-address-lines',
        None,
        'There’s a problem with the address for this letter',
        (
            'The address must be no more than 7 lines long.'
        ),
        (
            'Validation failed because the address must be no more than 7 lines long.'
        ),
    ),
    (
        'invalid-char-in-address',
        None,
        'There’s a problem with the address for this letter',
        (
            'Address lines must not start with any of the following characters: @ ( ) = [ ] ” \\ / , < > ~'
        ),
        (
            'Validation failed because address lines must not start with any of the following '
            'characters: @ ( ) = [ ] ” \\ / , < > ~'
        ),
    ),
])
def test_get_letter_validation_error_for_known_errors(
    client_request,
    error_message,
    invalid_pages,
    expected_title,
    expected_content,
    expected_summary,
):
    error = get_letter_validation_error(error_message, invalid_pages=invalid_pages, page_count=13)
    detail = BeautifulSoup(error['detail'], 'html.parser')
    summary = BeautifulSoup(error['summary'], 'html.parser')

    assert error['title'] == expected_title

    assert detail.text == expected_content
    if detail.select_one('a'):
        assert detail.select_one('a')['href'] == url_for('.letter_specification')

    assert summary.text == expected_summary
    if summary.select_one('a'):
        assert summary.select_one('a')['href'] == url_for('.letter_specification')
