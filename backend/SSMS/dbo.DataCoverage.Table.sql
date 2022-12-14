USE [PMFeeder]
GO
/****** Object:  Table [dbo].[DataCoverage]    Script Date: 21-Sep-22 7:17:58 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DataCoverage](
	[full_ticker] [nchar](20) NOT NULL,
	[datapoint_name] [nchar](15) NOT NULL,
	[start_coverage] [date] NOT NULL,
	[end_coverage] [date] NOT NULL,
 CONSTRAINT [IX_DataCoverage] UNIQUE CLUSTERED 
(
	[full_ticker] ASC,
	[datapoint_name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
