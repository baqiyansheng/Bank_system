DELIMITER !

DROP PROCEDURE IF EXISTS drop_bank;

CREATE PROCEDURE drop_bank(IN bank_ID VARCHAR(20), OUT error_message VARCHAR(255))
BEGIN
    DECLARE account_count INT; -- 还有余额的账户
    DECLARE loan_count INT; -- 未还清的贷款数量
    SELECT COUNT(*) INTO account_count FROM account WHERE `account`.`Bank_ID` = bank_ID AND `account`.`Balance` <> 0; -- 有余额的
    SELECT COUNT(*) INTO loan_count FROM loan WHERE `loan`.`Bank_ID` = bank_ID AND `loan`.`status` = 0; -- 未还清的贷款
    IF account_count = 0 AND loan_count = 0 THEN
        DELETE FROM account WHERE `account`.`Bank_ID` = bank_ID;
        DELETE FROM loan WHERE `loan`.`Bank_ID` = bank_ID;
        DELETE FROM bank WHERE `bank`.`Bank_ID` = bank_ID;
    ELSEIF account_count <> 0 THEN
        SET error_message = '该银行还有有余额的账户';
    ELSEIF loan_count <> 0 THEN
        SET error_message = '该银行还有未还清的贷款';
    END IF;
END 
!

DELIMITER;