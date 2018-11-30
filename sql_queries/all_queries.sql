-- ALL QUERIES, TO RUN IN THE SERVER IN A TMUX SESSION

-- Preprocess for general purpose tables (preprocessed): Network events and Tourist profile tables
create materialized view if not exists telecom_pt.preprocessed_union_all as
select
      enddate,
      client_id,
      CONCAT(
          cast(union_all.cell_id as varchar(16)),
          cast(union_all.lac as varchar(16)),
          cast(union_all.protocol as varchar(16))
          ) as cell_ref,
      substring(cast(union_all.mccmnc as varchar(16)),1,3) as mcc,
      uniques_mcc.mnew_country as origin
from telecom_pt.union_all
left join (select distinct(cast(mccmnc.mmcc as varchar(16))) as mcc, mnew_country from telecom_pt.mccmnc) as uniques_mcc
on substring(cast(union_all.mccmnc as varchar(16)),1,3)=uniques_mcc.mcc;


-- Generate master table: Table with all the events

create materialized view if not exists telecom_pt.master_table as
select
    preprocessed_union_all.enddate as event_date,
    extract(day from preprocessed_union_all.enddate) as day_of_month,
    extract(hour from preprocessed_union_all.enddate) as hour_of_day,
    extract(minute from preprocessed_union_all.enddate) as minute_of_hour,
    preprocessed_union_all.client_id,
    preprocessed_union_all.origin,
    preprocessed_union_all.cell_ref,
    label,
    centroide_latitude,
    centroide_longitude,
    distrito,
    concelho,
    municipio,
    poi
from telecom_pt.preprocessed_union_all
left join (
            select
                concat(cast(ci as varchar(16)),cast(cast(lac as int) as varchar(16)),cast(cast(protocol_ as int) as varchar(16))
                       ) as cell_ref,
                region_labels.municipio,
                region_labels.distrito,
                region_labels.concelho,
                region_labels.poi,
              cellid_anchors.cellid as label,
              site_lookup.centroide_latitude,
                site_lookup.centroide_longitude
            from telecom_pt.site_lookup
            left join telecom_pt.cellid_anchors
            on concat(cast(ci as varchar(16)),cast(cast(lac as int) as varchar(16)),cast(cast(protocol_ as int) as varchar(16)))=cast(cellid_anchors.cellid2 as varchar(16))
            left join telecom_pt.region_labels
            on concat(cast(ci as varchar(16)),cast(cast(lac as int) as varchar(16)),cast(cast(protocol_ as int) as varchar(16))) = region_labels.cell_id
            ) as nodes_anchors
on preprocessed_union_all.cell_ref=nodes_anchors.cell_ref
order by enddate
;


/*
create materialized view if not exists telecom_pt.master_table as
select
    sub_main3.event_date,
    sub_main3.day_of_month,
    sub_main3.hour_of_day,
    sub_main3.minute_of_hour,
    sub_main3.client_id,
    sub_main3.origin,
    cell_ref,
    sub_main3.centroide_latitude,
    sub_main3.centroide_longitude,
    region_labels.distrito,
    region_labels.concelho,
    region_labels.municipio,
    sub_main3.label as anchor


from
    (select sub_main2.enddate as event_date,
            extract(day from sub_main2.enddate) as day_of_month,
            extract(hour from sub_main2.enddate) as hour_of_day,
            extract(minute from sub_main2.enddate) as minute_of_hour,
            sub_main2.client_id,
            sub_main2.origin,
            nodes_anchors.label,
            nodes_anchors.centroide_latitude,
            nodes_anchors.centroide_longitude,
            sub_main2.cell_ref
    from (select * from telecom_pt.preprocessed_union_all limit 5000) as sub_main2

    left join  (
            select distinct(
                concat(cast(ci as varchar(16)),cast(cast(lac as int) as varchar(16)),cast(cast(protocol_ as int) as varchar(16)))
                       ) as cell_ref,
               cellid_anchors.cellid as label,
               site_lookup.centroide_latitude, site_lookup.centroide_longitude
            from telecom_pt.site_lookup
            left join telecom_pt.cellid_anchors
            on concat(cast(ci as varchar(16)),cast(cast(lac as int) as varchar(16)),cast(cast(protocol_ as int) as varchar(16)))=cast(cellid_anchors.cellid2 as varchar(16))
            ) as nodes_anchors
    on cast(sub_main2.cell_ref as varchar(16)) = cast(nodes_anchors.cell_ref as varchar(16))
    ) as sub_main3
left join
    telecom_pt.region_labels
on sub_main3.cell_ref = region_labels.cell_id
ORDER BY event_date ASC
;
*/

-- Preprocessing for roamers table
create materialized view if not exists telecom_pt.pre_roamers_table as
select
    sub_main3.client_id,
    sub_main3.first_contact,
    sub_main3.last_contact,
    sub_main3.country_of_origin,
    sub_main3.length_of_stay,
    extract(epoch from sub_main3.length_of_stay)/86400.0 as days_of_stay, -- changed since last run, fixes 0 error in rounded days of stay
    sub_main3.weekday_of_arrival,
    sub_main3.arrival_location as arrival_ci,
    region_labels.concelho as arrival_concelho,
    region_labels.distrito as arrival_distrito,
    region_labels.poi as arrival_poi,
    cellid_anchors.cellid as arrival_anchor_label
from (
    select sub_main2.client_id,
        max(sub_main2.enddate) as last_contact,
        min(sub_main2.enddate) as first_contact,
        sub_main2.origin as country_of_origin,
        max(sub_main2.enddate)-min(sub_main2.enddate) as length_of_stay,
        sub_main2.arrival_location,
        extract(isodow from min(sub_main2.enddate)) as weekday_of_arrival --Monday=1 Sunday=7
    from
        (
        select
            sub_main.client_id,
            sub_main.enddate,
            sub_main.origin,
            first_value(cell_ref) over (partition by client_id order by enddate asc) as arrival_location
        from telecom_pt.preprocessed_union_all as sub_main
        group by client_id, cell_ref, enddate, origin
        ) as sub_main2
    group by client_id, arrival_location, origin
    ) as sub_main3
left join telecom_pt.region_labels on sub_main3.arrival_location = region_labels.cell_id
left join telecom_pt.cellid_anchors on sub_main3.arrival_location = cellid_anchors.cellid2;


-- Second preprocessing for roamers table
create materialized view if not exists telecom_pt.second_pre_roamers_table as
select
    master_table.client_id,
    count(distinct(master_table.concelho)) as count_concelhos_visited,
    count(distinct(master_table.distrito)) as count_distritos_visited,
    count(distinct(master_table.poi)) as count_poi_visited,
    count(distinct(master_table.label)) as count_anchors_visited
from telecom_pt.master_table
group by client_id;


-- Generate movement sequences: POI
create materialized view if not exists telecom_pt.pre_sequences_poi as
WITH marked AS (
  SELECT
    *,
    (ROW_NUMBER()   OVER (PARTITION BY client_id      ORDER BY event_date)
     - ROW_NUMBER() OVER (PARTITION BY client_id, poi ORDER BY event_date)) as include_returns
  FROM telecom_pt.master_table as pre_main
)
SELECT
  marked.client_id,
  min(marked.event_date) as arrived_to_location_at,
  max(marked.event_date) as left_location_at,
  max(marked.event_date)-min(marked.event_date) as time_length,
  marked.poi
FROM
  marked
GROUP BY
  client_id, poi, include_returns
order by
  client_id, min(event_date)
;



-- Generate movement sequences: MUNICIPIOS
create materialized view if not exists telecom_pt.pre_sequences_municipios as
WITH marked AS (
  SELECT
    *,
    (ROW_NUMBER() OVER (PARTITION BY client_id             ORDER BY event_date)
     - ROW_NUMBER() OVER (PARTITION BY client_id, municipio ORDER BY event_date)) as include_returns
  FROM telecom_pt.master_table as pre_main
)
SELECT
  marked.client_id,
  min(marked.event_date) as arrived_to_location_at,
  max(marked.event_date) as left_location_at,
  max(marked.event_date)-min(marked.event_date) as time_length,
  marked.municipio
FROM
  marked
GROUP BY
  client_id, municipio, include_returns
order by
  client_id, min(event_date)
;



-- Generate movement sequences: CONCELHOS
create materialized view if not exists telecom_pt.pre_sequences_concelhos as
WITH marked AS (
  SELECT
    *,
    (ROW_NUMBER() OVER (PARTITION BY client_id             ORDER BY event_date)
     - ROW_NUMBER() OVER (PARTITION BY client_id, concelho ORDER BY event_date)) as include_returns
  FROM telecom_pt.master_table as pre_main
)
SELECT
  marked.client_id,
  min(marked.event_date) as arrived_to_location_at,
  max(marked.event_date) as left_location_at,
  max(marked.event_date)-min(marked.event_date) as time_length,
  marked.concelho
FROM
  marked
GROUP BY
  client_id, concelho, include_returns
order by
  client_id, min(event_date)
;


-- Generate movement sequences: DISTRITOS
create materialized view if not exists telecom_pt.pre_sequences_distritos as
WITH marked AS (
  SELECT
    *,
    (ROW_NUMBER() OVER (PARTITION BY client_id             ORDER BY event_date)
     - ROW_NUMBER() OVER (PARTITION BY client_id, distrito ORDER BY event_date)) as include_returns
  FROM telecom_pt.master_table as pre_main
)
SELECT
  marked.client_id,
  min(marked.event_date) as arrived_to_location_at,
  max(marked.event_date) as left_location_at,
  max(marked.event_date)-min(marked.event_date) as time_length,
  marked.distrito
FROM
  marked
GROUP BY
  client_id, distrito, include_returns
order by
  client_id, min(event_date)
;


-- Generate movement sequences: LABELS
create materialized view if not exists telecom_pt.pre_sequences_labels as
WITH marked AS (
  SELECT
    *,
    (ROW_NUMBER() OVER (PARTITION BY client_id             ORDER BY event_date)
     - ROW_NUMBER() OVER (PARTITION BY client_id, label ORDER BY event_date)) as include_returns
  FROM (select * from telecom_pt.master_table where label!='') as pre_main
)
SELECT
  marked.client_id,
  min(marked.event_date) as arrived_to_location_at,
  max(marked.event_date) as left_location_at,
  max(marked.event_date)-min(marked.event_date) as time_length,
  marked.label
FROM
  marked
GROUP BY
  client_id, label, include_returns
order by
  client_id, min(event_date)
;


-- Generate final sequences table: for all types of labels
create materialized view if not exists telecom_pt.sequences_table as
select
    concelhos.client_id,
    concelhos.concelhos_sequence,
    distritos.distritos_sequence,
    municipios.municipios_sequence,
    poi.poi_sequence,
    anchors.anchors_sequence

from
    (
        select
            client_id,
            array_to_string(array_agg(concelho), ',') as concelhos_sequence
        from telecom_pt.pre_sequences_concelhos
        WHERE
            time_length > interval '2 minutes'
        group by client_id
    ) as concelhos
left join
    (
        select
            client_id,
            array_to_string(array_agg(distrito), ',') as distritos_sequence
        from telecom_pt.pre_sequences_distritos
        WHERE
            time_length > interval '60 minutes'
        group by client_id
    ) as distritos
on concelhos.client_id=distritos.client_id
left join
    (
        select
            client_id,
            array_to_string(array_agg(municipio), ',') as municipios_sequence
        from telecom_pt.pre_sequences_municipios
        WHERE
            time_length > interval '30 minutes'
        group by client_id
    ) as municipios
on concelhos.client_id=municipios.client_id
left join
    (
        select
            client_id,
            array_to_string(array_agg(label), ',') as anchors_sequence
        from telecom_pt.pre_sequences_labels
        WHERE
            time_length > interval '30 minutes'
        group by client_id
    ) as anchors
on concelhos.client_id=anchors.client_id
left join
    (
        select
            client_id,
            array_to_string(array_agg(poi), ',') as poi_sequence
        from telecom_pt.pre_sequences_poi
        WHERE
            time_length > interval '30 minutes'
        group by client_id
    ) as poi
on concelhos.client_id=poi.client_id
;





-- Generate final roamers table: Table with the profiles of all tourists that connected to NOS in August
create materialized view if not exists telecom_pt.roamers_table as
select
                pre_roamers_table.client_id,
                pre_roamers_table.first_contact,
                pre_roamers_table.last_contact,
                pre_roamers_table.country_of_origin,
                pre_roamers_table.length_of_stay,
                pre_roamers_table.days_of_stay,
                pre_roamers_table.weekday_of_arrival,
                pre_roamers_table.arrival_ci,
                pre_roamers_table.arrival_concelho,
                pre_roamers_table.arrival_distrito,
                pre_roamers_table.arrival_anchor_label,
                site_lookup.centroide_latitude as arrival_lat,
                site_lookup.centroide_longitude as arrival_lon,
                second_pre_roamers_table.count_concelhos_visited,
                second_pre_roamers_table.count_distritos_visited,
                second_pre_roamers_table.count_anchors_visited,
                sequences_table.anchors_sequence,
                sequences_table.concelhos_sequence,
                sequences_table.distritos_sequence,
                sequences_table.municipios_sequence,
                sequences_table.poi_sequence
from telecom_pt.pre_roamers_table
left join telecom_pt.site_lookup
on cast(arrival_ci as varchar(16)) = concat(cast(ci as varchar(16)),cast(cast(lac as int) as varchar(16)),cast(cast(protocol_ as int) as varchar(16)))
left join telecom_pt.second_pre_roamers_table
    on pre_roamers_table.client_id = second_pre_roamers_table.client_id
left join telecom_pt.sequences_table
    on pre_roamers_table.client_id = sequences_table.client_id

;


-- Data ready for visualization: Number of tourists per length of stay
create materialized view if not exists telecom_pt.viz_tourists_per_length_stay as
select
        round(roamers_table.days_of_stay) as days_of_stay,
        count(*) as tourists_per_days_of_stay
from telecom_pt.roamers_table
where extract(day from roamers_table.first_contact)!=1 or extract(day from roamers_table.last_contact)!=31
group by round(roamers_table.days_of_stay);


-- Data ready for visualization: Tourists per country of origin
create materialized view if not exists telecom_pt.viz_tourists_per_origin as
select roamers_table.country_of_origin,
        count(*) as tourists_per_origin,
        avg(roamers_table.length_of_stay) as avg_length_of_stay
from telecom_pt.roamers_table
group by roamers_table.country_of_origin;


-- Data ready for visualization: Average stay per district
create materialized view if not exists telecom_pt.viz_avgstay_per_district as
select
    master_table.distrito,
    count(distinct(master_table.client_id)) as count_of_tourists,
    avg(roamers_table.length_of_stay) as avg_stay_in_pt
from
    telecom_pt.master_table
left join
    telecom_pt.roamers_table
on
    master_table.client_id = roamers_table.client_id
group by master_table.distrito;



create materialized view if not exists telecom_pt.viz_weekday_arrival as
select
    weekday_of_arrival,
    count(client_id) as number_of_tourists
from telecom_pt.roamers_table
group by weekday_of_arrival;


create materialized view if not exists telecom_pt.viz_weekday_departure as
select
    extract(isodow from last_contact) as weekday_of_departure,
    count(client_id) as number_of_tourists
from telecom_pt.roamers_table
group by extract(isodow from last_contact);



-- Number of tourists in portugal per day per nationality
create materialized view if not exists viz_tourists_per_origin_per_day as
select
    day_of_month as day,
    origin,
    count(distinct(client_id)) as count_of_tourists
from telecom_pt.master_table
group by day_of_month, origin;


-- Data ready for visualization: Tourists per day
create materialized view if not exists telecom_pt.viz_tourists_per_day as
select
    master_table.day_of_month,
    master_table.distrito,
    count(distinct(master_table.client_id)) as daily_tourist_count
from telecom_pt.master_table
group by master_table.day_of_month, master_table.distrito;

-- Flows visualization for days with cruise ships (1 and 29) vs days without cruise ships (5 and 28)
create materialized view if not exists telecom_pt.viz_cruise_ships as
select
    master_table.client_id,
    master_table.origin, -- to give colors to observations
    master_table.day_of_month,
    master_table.hour_of_day,
    master_table.minute_of_hour,
    avg(master_table.centroide_latitude) as lat,
    avg(master_table.centroide_longitude) as lon
from telecom_pt.master_table
where (day_of_month in (1,5,28,29)) and (distrito='Lisboa')
group by client_id, origin, day_of_month,hour_of_day, minute_of_hour;


create materialized view if not exists telecom_pt.edges_for_sna as
select
    from_,
    to_,
    sum(flow) as flows
from
    (
        select
            client_id,
            lag(municipio, 1) over (partition by client_id order by arrived_to_location_at) as from_,
            municipio as to_,
            1 as flow
            --arrived_to_location_at,
            --left_location_at,
            --time_length
        from
            (
                select *
                from telecom_pt.pre_sequences_municipios
                where time_length > interval '5 minutes'
            ) as sub_main
    ) as sub_main2
where from_ != to_ --or from_ is null
group by from_, to_;


create materialized view if not exists telecom_pt.nodes_for_sna as
select
    municipio,
    concelho,
    distrito,
    poi
from telecom_pt.region_labels
group by municipio, concelho, distrito, poi
;


create materialized view if not exists telecom_pt.viz_length_per_district as
select
    sub_main.distrito,
    avg(roamers_table.length_of_stay) as avg_stay_in_pt
from
  (
    select
      master_table.distrito,
      master_table.client_id
     from
      telecom_pt.master_table
     group by
       client_id,distrito
  ) as sub_main
left join
    telecom_pt.roamers_table
on
    sub_main.client_id = roamers_table.client_id
group by
    sub_main.distrito
;


create materialized view if not exists telecom_pt.viz_data_stories_test as
select
  country_of_origin,
  avg(length_of_stay) as average_length_of_stay,
  avg(extract(day from first_contact)) as avg_arrival_day,
  avg(extract(day from last_contact)) as avg_departure_day,
  arrival_concelho,
  count(arrival_concelho) as count_arrival_concelho,
  arrival_distrito,
  count(arrival_distrito) as count_arrival_distrito,
  arrival_anchor_label,
  count(arrival_anchor_label) as count_arrival_label
from telecom_pt.roamers_table
where
  distritos_sequence like '%Lisboa%' and country_of_origin='France'
group by country_of_origin,arrival_concelho,arrival_distrito,arrival_anchor_label
;

/*
create materialized view if not exists telecom_pt.___test_data_stories_sequences as
select client_id, event_date, centroide_latitude, centroide_longitude, municipio
from (select * from telecom_pt.master_table where extract(day from event_date)>8 and extract(day from event_date)<14) as lel
where
    client_id=6826968
order by event_date
;
*/

