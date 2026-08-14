-- 02-seed.sql: 向数据库插入测试数据。
-- 这些医院、地址、车辆均为虚构数据。


INSERT INTO dispatch.hospital(
    hospital_id,
    hospital_name,
    district
)
VALUES
    ('H001', '市中心医院', '金平区'),
    ('H002', '市潮阳医院', '潮阳区'),
    ('H003', '市龙湖医院', '龙湖区'),
    ('H004', '市澄海医院', '澄海区'),
    ('H005', '市濠江医院', '濠江区');

-- 使用CTE临时定义12条典型警情

WITH curated(
    case_id,
    hours_ago,
    district,
    address_masked,
    event_type,
    chief_complaint,
    case_summary,
    age_group,
    gender,
    hospital_id,
    dispatch_delay,
    travel_delay
) AS (
    VALUES
        (
            'CASE-DEMO-0001',
            6,
            '潮阳区',
            '中关村某商场附近',
            '急病',
            '老人突然昏厥、呼吸困难',
            '商场内老人突然昏厥，伴呼吸困难和出冷汗',
            '老年',
            '男',
            'H002',
            180,
            720
        ),
        (
            'CASE-DEMO-0002',
            30,
            '龙湖区',
            '学院路某小区附近',
            '急病',
            '胸闷、出冷汗、意识模糊',
            '老人在家胸闷出冷汗，随后意识模糊，家属报警',
            '老年',
            '女',
            'H002',
            240,
            660
        ),
        (
            'CASE-DEMO-0003',
            54,
            '金平区',
            '建国路某写字楼附近',
            '急病',
            '青年突发呼吸困难',
            '写字楼内人员突发胸闷及呼吸困难但意识清楚',
            '青年',
            '女',
            'H001',
            150,
            540
        ),
        (
            'CASE-DEMO-0004',
            78,
            '澄海区',
            '南苑路某路口附近',
            '交通事故',
            '两车碰撞，有人头部受伤',
            '雨天道路湿滑导致两车碰撞，一人头部外伤',
            '中年',
            '男',
            'H004',
            360,
            840
        ),
        (
            'CASE-DEMO-0005',
            102,
            '金平区',
            '西北旺某公园附近',
            '外伤',
            '路面结冰滑倒，手臂疼痛',
            '低温天气路面结冰，行人滑倒后手臂无法活动',
            '中年',
            '女',
            'H002',
            310,
            760
        ),
        (
            'CASE-DEMO-0006',
            126,
            '濠江区',
            '复兴门某地铁口附近',
            '外伤',
            '老人雪天摔伤无法站立',
            '雪后道路结冰，老人摔倒后髋部疼痛无法站立',
            '老年',
            '女',
            'H003',
            280,
            700
        ),
        (
            'CASE-DEMO-0007',
            150,
            '潮阳区',
            '东直门某学校附近',
            '儿科',
            '儿童高热并抽搐',
            '儿童持续高热后短暂抽搐，家长拨打急救电话',
            '儿童',
            '男',
            'H005',
            120,
            480
        ),
        (
            'CASE-DEMO-0008',
            174,
            '龙湖区',
            '望京某餐厅附近',
            '急病',
            '进食后呼吸急促、皮疹',
            '就餐后出现全身皮疹并呼吸急促，疑似严重过敏',
            '青年',
            '女',
            'H001',
            165,
            600
        ),
        (
            'CASE-DEMO-0009',
            198,
            '濠江区',
            '丽泽路某工地附近',
            '外伤',
            '高处坠落，腿部受伤',
            '施工人员从低处坠落，腿部疼痛且活动受限',
            '中年',
            '男',
            'H004',
            205,
            690
        ),
        (
            'CASE-DEMO-0010',
            222,
            '金平区',
            '金融街某办公楼附近',
            '急病',
            '突发胸痛、恶心',
            '办公人员突发持续胸痛并伴恶心和冷汗',
            '中年',
            '男',
            'H003',
            190,
            570
        ),
        (
            'CASE-DEMO-0011',
            246,
            '澄海区',
            '安定门某胡同附近',
            '急病',
            '老人意识不清',
            '独居老人被发现意识不清，呼叫反应较弱',
            '老年',
            '未知',
            'H005',
            420,
            800
        ),
        (
            'CASE-DEMO-0012',
            270,
            '龙湖区',
            '三里屯某商场附近',
            '其他',
            '酒后倒地但有呼吸',
            '公共场所一人酒后倒地，可见自主呼吸',
            '青年',
            '男',
            'H001',
            330,
            630
        )
),
inserted_cases AS(
        INSERT INTO dispatch.alarm_case (
        case_id,
        alarm_time,
        district,
        address_masked,
        event_type,
        chief_complaint,
        case_summary,
        caller_age_group,
        caller_gender
    )
    SELECT
        case_id,
        now() - make_interval(hours => hours_ago),
        district,
        address_masked,
        event_type,
        chief_complaint,
        case_summary,
        age_group,
        gender
    FROM curated
    RETURNING case_id
)
INSERT INTO dispatch.mabulance_dispatch (
    case_id,
    hospital_id,
    ambulance_code_masked,
    dispatch_time,
    arrival_time,
    finish_time,
    dispatch_status
)
SELECT
    c.case_id,
    c.hospital_id,
    'AMB-***-' || right(c.case_id, 2),

    now()
        - make_interval(hours => c.hours_ago)
        + make_interval(secs => c.dispatch_delay),

    now()
        - make_interval(hours => c.hours_ago)
        + make_interval(secs => c.travel_delay),

    now()
        - make_interval(hours => c.hours_ago)
        + make_interval(secs => c.travel_delay + 1800),

    '已完成'

FROM curated AS c
JOIN inserted_cases AS i 
    USING(case_id);

-- 批量生成1000条模拟数据

WITH generated AS(
    SELECT
        g,

        'CASE-SIM-' || lpad(g::text, 6, '0') AS case_id,

        now() - make_interval(hours => g * 3) AS alarm_time,

        (ARRAY[
            '金平区',
            '龙湖区',
            '澄海区',
            '濠江区',
            '潮阳区'
        ])[1 + g % 5] AS district,

        (ARRAY[
            '某小区附近',
            '某商场附近',
            '某道路附近',
            '某公园附近'
        ])[1 + g % 4] AS address_masked,

        (ARRAY[
            '急病',
            '外伤',
            '交通事故',
            '儿科',
            '其他'
        ])[1 + g % 5] AS event_type,

        (ARRAY[
            '头晕乏力',
            '胸痛胸闷',
            '摔倒受伤',
            '交通碰撞受伤',
            '儿童持续高热'
        ])[1 + g % 5] AS complaint,

        (ARRAY[
            '患者头晕乏力，家属请求急救',
            '患者胸痛胸闷并伴出汗',
            '行人摔倒后肢体疼痛',
            '道路交通事故后有人受伤',
            '儿童持续高热，精神状态欠佳'
        ])[1 + g % 5] AS summary,

        (ARRAY[
            '儿童',
            '青年',
            '中年',
            '老年'
        ])[1 + g % 4] AS age_group,

        (ARRAY[
            '男',
            '女',
            '未知'
        ])[1 + g % 3] AS gender,

        'H00' || (1 + g % 5)::text AS hospital_id,

        60 + (g * 37) % 480 AS dispatch_delay,

        420 + (g * 53) % 1200 AS response_delay

    FROM generate_series(1, 1000) AS g
),
inserted_cases AS (
    INSERT INTO dispatch.alarm_case (
               case_id,
        alarm_time,
        district,
        address_masked,
        event_type,
        chief_complaint,
        case_summary,
        caller_age_group,
        caller_gender
    )
    SELECT
        case_id,
        alarm_time,
        district,
        address_masked,
        event_type,
        complaint,
        summary,
        age_group,
        gender
    FROM generated
    RETURNING case_id
)
INSERT INTO dispatch.ambulance_dispatch (
    case_id,
    hospital_id,
    ambulance_code_masked,
    dispatch_time,
    arrival_time,
    finish_time,
    dispatch_status
)
SELECT
    g.case_id,
    g.hospital_id,
    'AMB-***-' || lpad((g.g % 30)::text, 2, '0'),

    g.alarm_time
        + make_interval(secs => g.dispatch_delay),

    g.alarm_time
        + make_interval(secs => g.response_delay),

    g.alarm_time
        + make_interval(secs => g.response_delay + 1200),

    '已完成'

FROM generated AS g
JOIN inserted_cases AS i
    USING (case_id);

-- 更新表的统计信息，帮助PostgreSQL选择更合适的查询方案。
ANALYZE dispatch.alarm_case;
ANALYZE dispatch.ambulance_dispatch;