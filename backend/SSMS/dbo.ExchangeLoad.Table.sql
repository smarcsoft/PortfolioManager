USE [PMFeeder]
GO
/****** Object:  Table [dbo].[ExchangeLoad]    Script Date: 21-Sep-22 7:17:58 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ExchangeLoad](
	[id] [numeric](18, 0) IDENTITY(1,1) NOT NULL,
	[code] [nchar](15) NOT NULL,
	[part] [smallint] NOT NULL,
	[load_time] [datetime] NOT NULL,
 CONSTRAINT [PK_ExchangeLoad] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
