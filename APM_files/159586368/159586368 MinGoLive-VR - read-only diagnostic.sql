-- Pier Walk / EID 139041614. Read-only diagnostic derived from the supplied MinGoLive-VR.
-- Creator metadata omitted; property-level metrics are not per-unit ARI confirmation.
WITH pier_walk_property AS (
SELECT
SG.SKUGroupID,
SG.cancelpenaltyminutecnt,
SG.RatePlanCostPriceTypeID,
SG.ChildExtraPersonChargeBool,
SG.LOSExtensionBool,
SG.LARExtranetEnabledBool,
SG.LAREnabledBool,
SG.CommissionMask,
SG.LARTaxesIncludedBool,
SG.ActiveStatusTypeID,
SG.SellStateID,
SG.ARIEnabledBool,
SG.ECLEnabledBool,
SG.expediacollectsupplieroperatingmodel,
SG.LARFeesIncludedBool,
SG.BusinessModelMask,
SG.CurrencyCodeDefault,
SG.excludefrompkgbool,
SG.PackageUpgradeAllowedBool,
SG.GroupReconciliationBool,
SG.SKUGroupMarginDeltaStateID,
SG.CutOffTimeMinuteCnt,
SG.packagemultipropertyallowedbool,
SG.InventoryReturnMinuteCntDefault,
SG.ExpediaCollectSupplierRemittanceType,
SUCC.SUCCEnabledBool,
SGN.BookingStateID,
sgbmma.BusinessModelMaskActive,
SGL.CreateDate,
SGL.CreateTUID,
egp.Property_Name,
egp.Structure_Category_Name,
egp.Brand_Name,
egp.City_Name,
egp.Country_Code,
egp.market_super_region_name,
egp.market_region_name,
egp.market_name,
egp.market_sub_market_name,
egp.State_Province_Name,
egp.Parent_Chain_Name,
egp.Structure_Type_Name,
egp.Postal_code,
egp.First_Address_Line,
egp.star_rating_internal,
egp.market_manager_email_address,
egp.parent_chain_account_type_name,
egp.active_property_bool,
lcm_tsp.bookability_bool,
lcm_tsp.update_datetime as TSP_24_UpdateDate,
HC.responderid,
HC.bn_enabled,
HC.hotelcode,
HC.chaincode,
HC.brandcode,
HC.ar_ari_system,
HC.ar_ari_sfid_system,
hc.ar_ari_sfid_vendor,
hc.br_bn_sfid_system,
hc.br_bn_sfid_vendor,
SGA.waivealltaxessettingmask,
SGA.autorenewalclosuredates,
SGA.projectedstopsellenddate,
SGA.ratematchenabledbool,
SGA.stopsellreasoncode
FROM
egdp_prod_supply.lodging_inventory_skugroup SG
LEFT OUTER JOIN egdp_prod_supply.lodging_inventory_skugrouplog SGL on SGL.SKUGroupID = SG.SKUGroupID AND SGL.LogActionTypeID = 1
--LEFT OUTER JOIN egdp_prod_supply.lodging_content_eg_provider_fact lcm_tsp ON  lcm_tsp.eg_property_id = HC.expediaid --AND lcm_tsp.Travel_Service_Provider_ID = 24 --AND lcm_tsp.bookability_bool = TRUE
LEFT OUTER JOIN egdp_prod_supply.lodging_profile_eg egp on egp.eg_property_id = SG.SKUGroupID
LEFT OUTER JOIN egdp_prod_supply.lodging_inventory_SKUGroupSUCC SUCC ON SUCC.SKUGroupID = SG.SKUGroupID
LEFT OUTER JOIN egdp_prod_supply.lodging_inventory_SKUGroupNotification sgn ON sgn.SKUGroupID = sg.SKUGroupID
LEFT OUTER JOIN egdp_prod_supply.lodging_inventory_SKUGroupBusinessModelMaskActive sgbmma ON sgbmma.SKUGroupID = SG.SKUGroupID
LEFT OUTER JOIN data_dw_dm.lodging_connectivity_profile HC on HC.eg_property_id = SG.SKUGroupID
LEFT OUTER JOIN egdp_prod_supply.lodging_content_eg_provider_fact lcm_tsp ON  lcm_tsp.eg_property_id = SG.SKUGroupID AND lcm_tsp.Travel_Service_Provider_ID = 24
LEFT OUTER JOIN egdp_prod_supply.lodging_inventory_skugroupattribute SGA
		ON SG.skugroupid = SGA.skugroupid
WHERE 1=1
--lower(HC.responderid) NOT IN ('vrbo','homeaway') AND 
--lower(egp.property_name) NOT LIKE '%eqc%' AND 
--lower(egp.city_name) NOT LIKE '%region test%'
--AND lower(parent_chain_name) like '%guestready%'; -- ensure search parameters are in all lowercase
--AND lower(HC.responderid) like '%shs_wyndham_inv_ec2%' -- ensure search parameters are in all lowercase
AND
SG.SKUGroupID IN (139041614)
),
RateLastUpdate AS
(
Select
SG.SKUGroupID,
Max(RPLCP.SupplierUpdateDate) RateLastUpdateDate,
MIN(RPLCP.StayDate) MinRateDate,
MAX(RPLCP.StayDate) MaxRateDate
from 
pier_walk_property SG
JOIN egdp_prod_supply.lodging_inventory_roomtype_noident RT ON RT.SKUGroupID = SG.SKUGroupID
JOIN egdp_prod_supply.lodging_inventory_rateplan_noident RP ON RP.RoomTypeId = RT.RoomTypeId
JOIN egdp_prod_supply.lodging_inventory_dailydata_RatePlanLevelCostPrice RPLCP ON RPLCP.RatePlanID = RP.RatePlanID
WHERE
RP.ActiveStatusTypeID = 2 AND RPLCP.StayDate >= Current_Date
GROUP BY
1
)

,RestrictionLastUpdate AS
(
Select
SG.SKUGroupID,
MAX(RPLR.SupplierUpdateDate) as RestrictionLastUpdateDate,
MIN(RPLR.StayDate) as MinAvailRestrictionDate,
MAX(RPLR.StayDate) as MaxAvailRestrictionDate
from
pier_walk_property SG
JOIN egdp_prod_supply.lodging_inventory_roomtype_noident RT ON RT.SKUGroupID = SG.SKUGroupID
JOIN egdp_prod_supply.lodging_inventory_rateplan_noident RP ON RP.RoomTypeID = RT.RoomTypeID
join egdp_prod_supply.lodging_inventory_dailydata_RatePlanLevelRestriction RPLR ON RPLR.RatePlanID = RP.RatePlanID
WHERE
RPLR.StayDate >= Current_Date AND RPLR.SellStateID = 0
GROUP BY 1
)

,InventoryLastUpdate AS
(
Select Distinct
SG.SKUGroupID,
Max(RTI.SupplierUpdateDate) InventoryLastUpdateDate,
MIN(RTI.RoomTypeInventoryDate) MinInventoryDate,
Max(RTI.RoomTypeInventoryDate) MaxInventoryDate
from 
pier_walk_property SG
JOIN egdp_prod_supply.lodging_inventory_roomtype_noident RT ON RT.SKUGroupID = SG.SKUGroupID
JOIN egdp_prod_supply.lodging_inventory_dailydata_RoomTypeInventory RTI ON RTI.RoomTypeID = RT.RoomTypeID AND RTI.RoomTypeInventorySellStateID <> 1 AND RTI.RoomTypeInventoryDate >= Current_Date
WHERE
RTI.RoomTypeInventoryDate >= Current_Date AND RTI.RoomTypeInventorySellStateID <> 1 AND
(
(RTI.RoomTypeInventorySellStateID NOT IN (2,3,4) AND RTI.RoomTypeInventoryCntAvailable > 0) OR
RTI.RoomTypeInventorySellStateID = 2
)
GROUP BY
1
)

,RatePlan_Active_Count AS
(
SELECT Distinct
sg.SKUGroupID,
(Select Count(Distinct RoomTypeID) RTC FROM egdp_prod_supply.lodging_inventory_RoomType_NoIdent RT2 WHERE RT2.ActiveStatusTypeID = 2 AND RT2.SKUGroupID = sg.SKUGrouPID ) as Active_RT,
Sum (Case When RP.ActiveStatusTypeID  = 2 Then 1 else 0 end) as Active_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.RatePlanTypeID = 524288 Then 1 else 0 end) as Standalone_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.RatePlanTypeID = 16777216 Then 1 else 0 end) as Package_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.RatePlanTypeID = 8388608 Then 1 else 0 end) as Corporate_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.RatePlanTypeID = 536870912 Then 1 else 0 end) as Wholesale_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.RatePlanTypeID = 1073741824 Then 1 else 0 end) as Wholesale_Package_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.ARIEnabledbool = 0 THEN 1 else 0 end) as Extranet_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.ARIEnabledbool = 1 THEN 1 else 0 end) as ARI_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.BusinessModelMask = 1 THEN 1 else 0 end) as Merchant_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.BusinessModelMask = 2 THEN 1 else 0 end) as Agency_RP,
Sum (Case When RP.ActiveStatusTypeID  = 2 AND RP.BusinessModelMask = 3 THEN 1 else 0 end) as Flex_RP
from 
pier_walk_property SG
join egdp_prod_supply.lodging_inventory_RoomType_NoIdent RT on RT.SKUGroupID = SG.SKUGroupID
join egdp_prod_supply.lodging_inventory_RatePlan_NoIdent RP on RP.RoomTypeID = RT.RoomTypeID and RP.ActiveStatusTypeID = 2
Group By 1
)

--Select * FROM RatePlan_Active_Count

,Total_Tax AS
(
SELECT
SG.SKUGroupID,
SUM(TT.TaxPerBookingRate) as Tax_Rate,
SUM(TT.TaxPerBookingAmt) as Tax_Amount,
Sum(TT.TaxPerDurationAmt) as Tax_Per_Night
FROM
pier_walk_property SG
JOIN egdp_prod_supply.lodging_inventory_TaxRate_NoIdent TT ON TT.SKUGroupID = SG.SKUGroupID
WHERE
TT.StartDate < Current_Date 
AND TT.EndDate >= Current_Date
Group BY
1
)
 
--Select * FROM Total_Tax

,SG_BM_TPID AS
(
SELECT
LC.SKUGroupID,
sgtbm.TPID,
t.TravelProductName,
sgtbm.BusinessModelMask,
sgtbm.UpdateDate,
sgtbm.UpdateTUID
FROM
pier_walk_property LC
Join egdp_prod_supply.lodging_inventory_SKUGroupTPIDBusinessModel sgtbm ON sgtbm.SKUGroupID = LC.SKUGroupID  
LEFT JOIN e4b_tst_all.channelandtpidmapping t ON t.TravelProductID = sgtbm.TPID
)
--Select * FROM SG_BM_TPID
  
,Property_TPIDs_EC AS
(
SELECT
(Select Count(Distinct SG_BM_TPID2.TPID) CNT FROM SG_BM_TPID SG_BM_TPID2 WHERE SG_BM_TPID2.SKUGroupID = SG_BM_TPID.SKUGroupID AND SG_BM_TPID2.BusinessModelMask = 2) as EC_Disabled_TPID_Count,
SG_BM_TPID.SKUGroupID,
SG_BM_TPID.TPID,
SG_BM_TPID.TravelProductName,
Case SG_BM_TPID.BusinessModelMask When 0 Then 'Both EC/HC'
When 1 then 'HC' When 2 then 'EC' End as Restricted_To
--SG_BM_TPID.UpdateDate as ChangeDate,
--SG_BM_TPID.UpdateTUID as UpdateTuid
FROM
SG_BM_TPID SG_BM_TPID
WHERE
SG_BM_TPID.BusinessModelMask = 2
GROUP BY
SG_BM_TPID.SKUGroupID,
SG_BM_TPID.TPID,
SG_BM_TPID.TravelProductName,
SG_BM_TPID.BusinessModelMask 
ORDER BY
SG_BM_TPID.SKUGroupID  
)
  
--Select * FROM Property_TPIDs_EC

,Property_TPIDs_HC AS
(
SELECT
(Select Count(Distinct SG_BM_TPID2.TPID) CNT FROM SG_BM_TPID SG_BM_TPID2 WHERE SG_BM_TPID2.SKUGroupID = SG_BM_TPID.SKUGroupID AND SG_BM_TPID2.BusinessModelMask = 1) as HC_Disabled_TPID_Count,
SG_BM_TPID.SKUGroupID,
SG_BM_TPID.TPID,
SG_BM_TPID.TravelProductName,
Case SG_BM_TPID.BusinessModelMask When 0 Then 'Both EC/HC'
When 1 then 'HC' When 2 then 'EC' End as Restricted_To
--SG_BM_TPID.UpdateDate as ChangeDate,
--SG_BM_TPID.UpdateTUID as UpdateTuid
FROM
SG_BM_TPID SG_BM_TPID
WHERE
SG_BM_TPID.BusinessModelMask = 1
GROUP BY
SG_BM_TPID.SKUGroupID,
SG_BM_TPID.TPID,
SG_BM_TPID.TravelProductName,
SG_BM_TPID.BusinessModelMask 
ORDER BY
SG_BM_TPID.SKUGroupID  
)

--Select * FROM Property_TPIDs_HC
  
,EC_Property_TPID_AGG AS
(
Select
SKUGroupID,
EC_Disabled_TPID_Count,
array_join(
        array_agg(
            concat(Cast(TPID as varchar), '-', TravelProductName) ORDER BY TPID ASC
        ), ', '
    ) as EC_Disabled_TPIDs
--array_join(array_agg(Cast(TPID as varchar) ORDER BY TPID ASC), ', ')
FROM Property_TPIDs_EC
GROUP BY 1,2
)
  
--Select * FROM EC_Property_TPID_AGG
  
,HC_Property_TPID_AGG AS
(
Select
SKUGroupID,
HC_Disabled_TPID_Count,
array_join(
        array_agg(
            concat(Cast(TPID as varchar), '-', TravelProductName) ORDER BY TPID ASC
        ), ', '
    ) as HC_Disabled_TPIDs
--array_join(array_agg(Cast(TPID as varchar) ORDER BY TPID ASC), ', ')
FROM Property_TPIDs_HC
GROUP BY 1,2
)

--Select * FROM HC_Property_TPID_AGG
 
,Photo_Count AS
(  
SELECT
exploded_associated_entities.id as property_id,
count(distinct m.ID) as Photo_Count
FROM egdp_prod_content.media_eg_content_platform_media_image_event m
CROSS JOIN UNNEST(associated_entities) AS exploded_associated_entities
CROSS JOIN UNNEST (m.tags) AS image_tags
JOIN pier_walk_property PI ON PI.SKUGroupID = Cast(exploded_associated_entities.ID as int)
where m.status.type=('STATUS_TYPE_PUBLISHED')
and exploded_associated_entities.type = 'ENTITY_TYPE_PROPERTY'
--and image_tags.key = 'subcategoryId'
and distributable=true
--and exploded_associated_entities.id in ('66282044',
--'20850297')
Group by 1  
)
--Select * FROM Photo_Count

,Room_Attributes AS
(
SELECT 
DISTINCT
RT.SKUGroupID,  
RT.RoomTypeID,
Count(Distinct scp.template_uuid) as Room_Attribute_Count,
MAX(CASE 
    WHEN scp.template_detail_uuid = '17f1a538-d2c7-46a9-8772-50c2ed8969c5' AND UPPER(scp.detail_status)='ACTIVE'
    THEN scp.detail_value
    END) as Number_of_Bathrooms,
MAX(CASE 
    WHEN scp.template_detail_uuid = '00e9f66f-408a-4f8f-ab0c-dcb43082cad7' AND UPPER(scp.detail_status)='ACTIVE'
    THEN scp.detail_value
    END) as Number_of_Bedrooms
--MAX(CASE WHEN scp.template_legacy_lcm_id = 4593 THEN scp.detail_value END) as Number_of_Bedrooms
FROM 
pier_walk_property ISC
JOIN egdp_prod_supply.lodging_inventory_roomtype_noident RT ON RT.SKUGroupID = ISC.SKUGroupID AND RT.ActiveStatusTypeID = 2
JOIN EGDP_PROD_SUPPLY.LODGING_CONTENT_EG_AMENITY AS scp ON scp.room_Unit_ID = Cast(RT.RoomTypeID as varchar) AND scp.Status = 'ACTIVE'
	 WHERE
   scp.DOMAIN_TYPE IN ('ROOM_UNIT')
	AND UPPER(scp.STATUS)='ACTIVE' -- ONLY ACTIVE ONES
   --AND SCP.eg_property_id = 36962826 
 GROUP BY 1,2
)
--select * FROM Room_Attributes

,Number_Of_Bedrooms_Bathrooms_Room_Agg AS
(
Select 
Distinct
RA.SKUGroupID,
  (Select  
array_join(
        array_agg(concat('[RoomTypeID: ', Cast(RA1.RoomTypeID as varchar), ' Count: ' , Cast(RA1.Number_of_Bathrooms as Varchar), ']')), ', '
    ) as Number_of_Bathrooms
FROM Room_Attributes RA1 WHERE RA.SKUGroupID = RA1.SKUGroupID
 ) as Number_of_Bathrooms,
  
  (Select  
array_join(
        array_agg(concat('[RoomTypeID: ', Cast(RA2.RoomTypeID as Varchar), ' Count: ' , Cast(RA2.Number_Of_Bedrooms as varchar), ']')), ', '
    ) as Number_of_Bedrooms
FROM Room_Attributes RA2 WHERE RA.SKUGroupID = RA2.SKUGroupID
 ) as Number_of_Bedrooms
  
FROM Room_Attributes RA  
)

--Select * FROM Number_Of_Bedrooms_Bathrooms_Room_Agg

,Property_Attributes AS
(
   SELECT DISTINCT
   scp.eg_property_id,
      Count(Distinct scp.template_uuid) as Property_Attribute_Count,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '70fdcabf-10f5-4a56-b290-e1e1d0b0eef4' AND UPPER(scp.detail_status)='ACTIVE' 
      THEN scp.detail_value
      END) as Number_Of_Units,
	MAX(CASE 
      WHEN scp.template_detail_uuid = '7ea68881-1135-4fb8-b8e9-bced28120a91' AND UPPER(scp.detail_status)='ACTIVE' 
      THEN scp.detail_value
      END) as Number_of_Bathrooms,
  MAX(CASE 

      WHEN scp.template_detail_uuid = '0219edd4-e3a2-4fb7-9dd9-2d74b70bbdc3' AND UPPER(scp.detail_status)='ACTIVE' 
      THEN scp.detail_value
      END) as Number_of_Bedrooms,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '7836a4bb-ea3a-434e-8b15-a918b6156a97' AND UPPER(scp.detail_status)='ACTIVE'
      THEN scp.detail_value
      END) as Property_Registry_Number,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '561d6af1-8be3-479d-803d-1bff08d6c413' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Damage_Deposit,
  MAX(CASE 
      WHEN scp.template_uuid = '52a3c65d-3318-4655-94c0-f08cfd447db6' 
      THEN 'Yes' Else 'No' 
      END) as Cleaning_Fee_Included_In_Rate,
  MAX(CASE 
      WHEN scp.template_uuid = '33463676-5d96-4b4d-80d2-14427c48ad6f'
      THEN 'Yes' else 'No' 
      END) as Contact_Property_in_Advance,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '03f68083-4553-4a14-bf25-2663141566b3' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(Cast(scp.detail_value as varchar),' hours')
      END) as Contact_Property_in_Advance_Detail,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '158f2296-7478-463d-b92b-57a94d9433ec' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Advance_Notice_Required_For_Late_Check_Time,
  MAX(CASE 
      WHEN scp.template_detail_uuid = 'b995a8b9-14e2-4244-869d-167b14b4033b' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Check_In_Start_Time,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '496e2c42-96e2-48dc-bdbf-0db798dfc022' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Check_In_End_Time,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '79dcc1d2-c8b4-469e-815b-d1e27fe37560' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Check_In_MinAge,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '9f472427-50b7-4117-a539-06fc13b8a8a3' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Late_Check_In_Start_Time,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '0a73e868-fb5a-4c16-bec3-2c18d81105bc' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Late_Check_In_End_Time,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '1e4daac0-3ecd-4dff-8a71-2b547373496c' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Late_Check_In_Fee,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '4f4f8e6b-d29c-4a82-bec3-369305bc253f' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      WHEN scp.template_detail_uuid = '3b9a5510-bb42-11e8-a355-529269fb1459' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Concat(scp.detail_name,': ',Cast(scp.detail_value as varchar))
      END) as Early_Check_In_Fee,
  MAX(CASE 
      WHEN scp.template_detail_uuid = '9ca546d2-c3d4-4359-8eec-d729427dac88' AND UPPER(scp.detail_status)='ACTIVE'
      THEN Cast(scp.detail_value as varchar)
      END) as Property_Will_Send_Guest_Email_In_Advance

   FROM pier_walk_property ISC 
   JOIN EGDP_PROD_SUPPLY.LODGING_CONTENT_EG_AMENITY AS scp ON scp.eg_property_id = ISC.SKUGroupID AND scp.Status = 'ACTIVE'
	 WHERE
   scp.DOMAIN_TYPE IN ('PROPERTY')
	 AND UPPER(scp.STATUS)='ACTIVE' -- ONLY ACTIVE ONES
   --AND SCP.eg_property_id = 36962826 
--   AND SCP.template_legacy_lcm_id IN (1073743379, 1073743378, 52, 1073742447, 1073743914, 2622, 2656, 1073743986, 5109, 3584, 1073743997, 1073744009, 1073742448)
 GROUP BY 1
 )

SELECT Distinct
PI.SKUGroupID as Expedia_ID,
PI.Property_Name,
--PI.Structure_Type_Name,
--PI.Market_Sub_Market_Name, 
--PI.Market_Name, 
--PI.Market_Region_Name,
--PI.Market_Super_Region_Name,
--PI.City_Name,
--PI.First_Address_Line,
--PI.Postal_Code,
CASE WHEN PI.Brand_Name IS NULL THEN '' ELSE PI.Brand_Name END AS Brand_Name,
PI.Country_Code,
PI.State_Province_Name,
Case PI.SellStateID
WHEN 1 THEN 'Stop Sell'
WHEN 2 THEN 'Free Sell'
WHEN 3 THEN 'Check Avail'
WHEN 4 THEN 'Free Sell Close'
ELSE 'Normal Sell'
END Stop_Sell_Status,
CASE WHEN PI.BusinessModelMask = 3 AND PI.BusinessModelMaskActive = 1 THEN 'HC fenced'
	WHEN PI.BusinessModelMask = 3 and PI.BusinessModelMaskActive = 2 THEN 'EC fenced'
	WHEN PI.BusinessModelMask = 3 and PI.BusinessModelMaskActive = 0 THEN 'EC/HC fenced'
	WHEN PI.BusinessModelMask = 3 and PI.BusinessModelMaskActive = 3 THEN 'Not fenced'
	WHEN PI.BusinessModelMask = 3 and PI.BusinessModelMaskActive IS NULL THEN 'Not fenced'
	WHEN PI.BusinessModelMask = 2 AND PI.BusinessModelMaskActive = 1 THEN 'HC fenced'
	WHEN PI.BusinessModelMask = 2 and PI.BusinessModelMaskActive = 2 THEN 'EC fenced'
	WHEN PI.BusinessModelMask = 2 and PI.BusinessModelMaskActive = 0 THEN 'EC/HC fenced'
	WHEN PI.BusinessModelMask = 2 and PI.BusinessModelMaskActive = 3 THEN 'Not fenced'
	WHEN PI.BusinessModelMask = 2 and PI.BusinessModelMaskActive IS NULL THEN 'Not fenced'
	WHEN PI.BusinessModelMask = 1 AND PI.BusinessModelMaskActive = 1 THEN 'HC fenced'
	WHEN PI.BusinessModelMask = 1 and PI.BusinessModelMaskActive = 2 THEN 'EC fenced'
	WHEN PI.BusinessModelMask = 1 and PI.BusinessModelMaskActive = 0 THEN 'EC/HC fenced'
	WHEN PI.BusinessModelMask = 1 and PI.BusinessModelMaskActive = 3 THEN 'Not fenced'
	WHEN PI.BusinessModelMask = 1 and PI.BusinessModelMaskActive IS NULL THEN 'Not fenced'
	ELSE 'No Inventory Rules Created'
END AS EC_HC_Fencing,
CASE 
WHEN TPEC.EC_Disabled_TPID_Count > 0 or TPHC.HC_Disabled_TPID_Count > 0 THEN True else False
END AS TPID_Fencing,
--ILU.MaxInventoryDate as Max_Inventory_StayDate,  
CASE WHEN PC.Photo_Count IS NULL THEN 0 Else PC.Photo_Count END as Image_count,
PAP.Number_of_Bedrooms as Property_Level_Number_of_Bedrooms,
PAP.Number_of_Bathrooms as Property_Level_Number_of_Bathrooms,
BAG.Number_of_Bedrooms as Room_Level_Number_Of_Bedrooms,
BAG.Number_of_Bathrooms Room_Level_Number_Of_Bathrooms,
CASE WHEN TT.Tax_Rate IS NOT NULL or TT.Tax_Amount IS NOT NULL OR TT.Tax_Per_Night IS NOT NULL THEN True else False END AS Taxes,
CASE WHEN RPC.Active_RT > 0 Then True else False END as Active_Products,
CASE 
WHEN date(ILU.MinInventoryDate) between date(CURRENT_DATE) and date(CURRENT_DATE + interval '365' day) Then TRUE else False END as Sufficent_Inventory
--PI.ar_ari_sfid_system
--SR.Star_Rating
FROM
pier_walk_property PI
LEFT OUTER JOIN Total_Tax TT ON TT.SKUGroupID = PI.SKUGroupID
LEFT OUTER JOIN Photo_Count PC ON Cast(PC.Property_ID as Int) = PI.SKUGroupID
LEFT OUTER JOIN HC_Property_TPID_AGG TPHC ON TPHC.SKUGroupID = PI.SKUGroupID
LEFT OUTER JOIN EC_Property_TPID_AGG TPEC ON TPEC.SKUGroupID = PI.SKUGroupID
LEFT OUTER JOIN RatePlan_Active_Count RPC ON RPC.SKUGroupID = PI.SKUGroupID
LEFT OUTER JOIN InventoryLastUpdate ILU ON ILU.SKUGroupID = PI.SKUGroupID
LEFT OUTER JOIN RateLastUpdate RLU ON RLU.SKUGroupID = PI.SKUGroupID
LEFT OUTER JOIN RestrictionLastUpdate RELU ON RELU.SKUGroupID = PI.SKUGroupID
LEFT OUTER JOIN Property_Attributes PAP ON PAP.eg_property_id = PI.SKUGroupID
LEFT OUTER JOIN Number_Of_Bedrooms_Bathrooms_Room_Agg BAG on BAG.SKUGroupID = PI.SKUGroupID limit 10000;