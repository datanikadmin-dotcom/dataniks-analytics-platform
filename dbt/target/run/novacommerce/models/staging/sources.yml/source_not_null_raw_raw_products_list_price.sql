
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select list_price
from "warehouse"."raw"."raw_products"
where list_price is null



  
  
      
    ) dbt_internal_test