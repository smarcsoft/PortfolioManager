USE [PMFeeder]
GO
/****** Object:  StoredProcedure [dbo].[update_ticker_coverage]    Script Date: 21-Sep-22 7:17:58 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		smarcsoft
-- Create date: 20 sept 2022
-- Description:	update the historical coverage of a ticker
-- =============================================
CREATE PROCEDURE [dbo].[update_ticker_coverage] 
	-- Add the parameters for the stored procedure here
	@full_ticker nvarchar(20),
	@datapoint_name nvarchar(15),
	@start_coverage date,
	@end_coverage date
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

     IF EXISTS (SELECT 1 FROM dbo.DataCoverage WHERE full_ticker = @full_ticker and datapoint_name = @datapoint_name)
	 BEGIN
		 UPDATE dbo.DataCoverage 
		 SET	full_ticker = @full_ticker,
				datapoint_name = @datapoint_name, 
				start_coverage =iif(@start_coverage < start_coverage, @start_coverage, start_coverage),
				end_coverage = iif(@end_coverage > end_coverage, @end_coverage, end_coverage)
		 WHERE full_ticker = @full_ticker and datapoint_name = @datapoint_name
	 END
	 ELSE
	 BEGIN
		 INSERT INTO dbo.DataCoverage
		 SELECT full_ticker = @full_ticker,
				datapoint_name = @datapoint_name,
				start_coverage = @start_coverage,
				end_coverage = @end_coverage;
	 END
	END
GO
