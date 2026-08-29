
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select ad_record_id
from "warehouse"."raw"."raw_ad_spend"
where ad_record_id is null



  
  
      
    ) dbt_internal_test