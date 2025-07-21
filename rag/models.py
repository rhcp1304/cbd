from django.db import models

class GoogleSheetData(models.Model):
    id = models.AutoField(primary_key=True)
    st_code = models.CharField(max_length=500, blank=True, null=True, db_column='ST_Code')
    store_name = models.CharField(max_length=500, blank=True, null=True, db_column='Store_Name')
    store_status = models.CharField(max_length=500, blank=True, null=True, db_column='Store_Status')
    city = models.CharField(max_length=500, blank=True, null=True, db_column='City')
    state = models.CharField(max_length=500, blank=True, null=True, db_column='State')
    zone = models.CharField(max_length=500, blank=True, null=True, db_column='Zone')
    hub = models.CharField(max_length=500, blank=True, null=True, db_column='Hub')
    circle = models.CharField(max_length=500, blank=True, null=True, db_column='Circle')
    bd_name = models.CharField(max_length=500, blank=True, null=True, db_column='BD_Name')
    state_head = models.CharField(max_length=500, blank=True, null=True, db_column='State_Head')
    zm_name = models.CharField(max_length=500, blank=True, null=True, db_column='ZM_Name')
    latitude = models.CharField(max_length=500, blank=True, null=True, db_column='Latitude')
    longitude = models.CharField(max_length=500, blank=True, null=True, db_column='Longitude')
    proto_rent_area_docusign_status = models.CharField(max_length=500, blank=True, null=True,
                                                       db_column='Proto_Rent_Area_Docusign_Status')
    proto = models.CharField(max_length=500, blank=True, null=True, db_column='Proto')
    rent = models.CharField(max_length=500, blank=True, null=True, db_column='Rent')
    size = models.CharField(max_length=500, blank=True, null=True, db_column='Size')
    presentation_date = models.CharField(max_length=500, blank=True, null=True, db_column='Presentation_Date')
    docusign_date = models.CharField(max_length=500, blank=True, null=True, db_column='Docusign_Date')
    recce_request_date = models.CharField(max_length=500, blank=True, null=True, db_column='Recce_Request_date')
    recce_aligned_date = models.CharField(max_length=500, blank=True, null=True, db_column='Recce_Aligned_Date')
    recee_uploaded_on_kissflow = models.CharField(max_length=500, blank=True, null=True,
                                                  db_column='Recee_uploaded_on_Kissflow')
    receetat = models.CharField(max_length=500, blank=True, null=True, db_column='ReceeTAT')
    merch = models.CharField(max_length=500, blank=True, null=True, db_column='Merch')
    layout_date = models.CharField(max_length=500, blank=True, null=True, db_column='Layout_Date')
    design_docket = models.CharField(max_length=500, blank=True, null=True, db_column='Design_Docket')
    panel_approval = models.CharField(max_length=500, blank=True, null=True, db_column='Panel_Approval')
    property_documents_status = models.CharField(max_length=500, blank=True, null=True,
                                                 db_column='Property_Documents_Status')
    panel_approval_property_document_tat = models.CharField(
        max_length=500, blank=True, null=True, db_column='Panel_Approval__Property_Document__TAT'
    )
    dd_completetion_date = models.CharField(max_length=500, blank=True, null=True, db_column='DD_Completetion_date')
    dd_tat = models.CharField(max_length=500, blank=True, null=True, db_column='DD_TAT')
    deal_closure = models.CharField(max_length=500, blank=True, null=True, db_column='Deal_Closure')
    final_signed_loi = models.CharField(max_length=500, blank=True, null=True, db_column='Final_Signed_LOI')
    final_signed_loi_tat = models.CharField(max_length=500, blank=True, null=True, db_column='Final_Signed_LOI_TAT')
    lease_agreement = models.CharField(max_length=500, blank=True, null=True, db_column='Lease_Agreement')
    lease_agreement_tat = models.CharField(max_length=500, blank=True, null=True, db_column='Lease_Agreement_TAT')
    green_channel = models.CharField(max_length=500, blank=True, null=True, db_column='Green_Channel')
    token_request_date = models.CharField(max_length=500, blank=True, null=True, db_column='Token_Request_Date')
    sunil_sir_approval = models.CharField(max_length=500, blank=True, null=True, db_column='Sunil_Sir_Approval')
    legal_approval = models.CharField(max_length=500, blank=True, null=True, db_column='Legal_Approval')
    finance_approval = models.CharField(max_length=500, blank=True, null=True, db_column='Finance_Approval')
    treasury_request_date = models.CharField(max_length=500, blank=True, null=True, db_column='Treasury_request_Date')
    token_release_date = models.CharField(max_length=500, blank=True, null=True, db_column='Token_Release_date')
    token_tat = models.CharField(max_length=500, blank=True, null=True, db_column='Token_TAT')
    possession_date = models.CharField(max_length=500, blank=True, null=True, db_column='Possession_Date')
    possession_month = models.CharField(max_length=500, blank=True, null=True, db_column='Possession_Month')
    pos_request_date = models.CharField(max_length=500, blank=True, null=True, db_column='Pos_Request_Date')
    pos_creation_date = models.CharField(max_length=500, blank=True, null=True, db_column='POS_Creation_Date')
    pos_tat_posposs = models.CharField(max_length=500, blank=True, null=True, db_column='POS_TAT_POSPOSS')
    store_handover_date = models.CharField(max_length=500, blank=True, null=True, db_column='Store_Handover_Date')
    finance_opening_date = models.CharField(max_length=500, blank=True, null=True, db_column='Finance_Opening_Date')
    remarks = models.CharField(max_length=500, blank=True, null=True, db_column='Remarks')
    presentation_to_docusign_tat = models.CharField(max_length=500, blank=True, null=True,
                                                    db_column='Presentation_to_Docusign_TAT')
    presentatio_to_recce_request_tat = models.CharField(max_length=500, blank=True, null=True,
                                                        db_column='Presentatio_to_Recce_Request_TAT')
    presentation_to_token_req = models.CharField(max_length=500, blank=True, null=True,
                                                 db_column='Presentation_To_Token_Req')
    site_status = models.CharField(max_length=500, blank=True, null=True, db_column='Site_Status')

    class Meta:
        managed = False
        db_table = 'google_sheet_data'
        verbose_name = "Imported Google Sheet Data Entry"
        verbose_name_plural = "Imported Google Sheet Data Entries"

    def __str__(self):
        return self.store_name or f"Sheet Data Entry {self.pk}"