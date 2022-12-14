USE [PMFeeder]
GO
/****** Object:  Table [dbo].[TickerLoad]    Script Date: 21-Sep-22 7:17:58 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[TickerLoad](
	[id] [numeric](18, 0) IDENTITY(1,1) NOT NULL,
	[exchange_load_id] [numeric](18, 0) NULL,
	[ticker_code] [nchar](20) NOT NULL,
	[data_point_name] [nchar](15) NOT NULL,
	[start_date] [date] NOT NULL,
	[end_date] [date] NOT NULL,
	[load_time] [datetime] NOT NULL,
 CONSTRAINT [PK_TickerLoad] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[TickerLoad]  WITH CHECK ADD  CONSTRAINT [FK_TickerLoad_ExchangeLoad] FOREIGN KEY([exchange_load_id])
REFERENCES [dbo].[ExchangeLoad] ([id])
GO
ALTER TABLE [dbo].[TickerLoad] CHECK CONSTRAINT [FK_TickerLoad_ExchangeLoad]
GO
