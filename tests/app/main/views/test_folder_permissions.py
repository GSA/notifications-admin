from tests.conftest import SERVICE_ONE_ID, sample_uuid


def test_select_all_button_works(
    client_request,
    mocker,
    mock_get_users_by_service,
    mock_get_invites_for_service,
):
    mocker.patch(
        "app.template_folder_api_client.get_template_folders",
        return_value=[
            {"id": "folder-1", "name": "Folder 1", "parent_id": None},
            {"id": "folder-2", "name": "Folder 2", "parent_id": None},
        ],
    )

    page = client_request.get(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=sample_uuid(),
    )

    button = page.select_one("button#select-all-folders")
    assert button is not None
    assert button.text.strip() in ["Select all", "Deselect all"]


def test_javascript_parent_child_logic_exists(
    client_request,
    mocker,
    mock_get_users_by_service,
    mock_get_invites_for_service,
):
    mocker.patch(
        "app.template_folder_api_client.get_template_folders",
        return_value=[
            {"id": "folder-1", "name": "Parent", "parent_id": None},
            {"id": "folder-2", "name": "Child", "parent_id": "folder-1"},
        ],
    )

    page = client_request.get(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=sample_uuid(),
        _test_page_title=False,
    )

    page_html = str(page)
    assert "handleParentSelection" in page_html
    assert "data-parent-id" in page_html
    assert "toggleSelectAll" in page_html


def test_hidden_from_platform_admins(
    mocker,
    client_request,
    platform_admin_user,
    mock_get_invites_for_service,
    mock_get_template_folders,
):
    mocker.patch("app.user_api_client.get_user", return_value=platform_admin_user)
    mocker.patch(
        "app.models.user.Users.client_method",
        return_value=[platform_admin_user],
    )

    page = client_request.get(
        "main.edit_user_permissions",
        service_id=SERVICE_ONE_ID,
        user_id=platform_admin_user["id"],
    )

    assert "Platform admin users can access all template folders" in page.text
    assert page.select_one("div#custom-folder-permissions") is None
