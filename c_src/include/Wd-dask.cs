using System.Runtime.InteropServices;
using System;

public delegate void CallbackDelegate();

public class WD_DASK
{
	//ADLink PCI Card Type
	public const ushort PCI_9820        = 1;
	public const ushort PXI_9816D       = 0x2;
	public const ushort PXI_9826D       = 0x3;
	public const ushort PXI_9846D       = 0x4;
	public const ushort PXI_9846DW      = 0x4;
	public const ushort PXI_9816H       = 0x5;
	public const ushort PXI_9826H       = 0x6;
	public const ushort PXI_9846H       = 0x7;
	public const ushort PXI_9846HW      = 0x7;
	public const ushort PXI_9816V       = 0x8;
	public const ushort PXI_9826V       = 0x9;
	public const ushort PXI_9846V       = 0xa;
	public const ushort PXI_9846VW      = 0xa;
	public const ushort PXI_9846VID     = 0xb;	
	//PCI 98x6 devices
	public const ushort PCI_9816D       = 0x12;
	public const ushort PCI_9826D       = 0x13;
	public const ushort PCI_9846D       = 0x14;
	public const ushort PCI_9846DW      = 0x14;
	public const ushort PCI_9816H       = 0x15;
	public const ushort PCI_9826H       = 0x16;
	public const ushort PCI_9846H       = 0x17;
	public const ushort PCI_9846HW      = 0x17;
	public const ushort PCI_9816V       = 0x18;
	public const ushort PCI_9826V       = 0x19;
	public const ushort PCI_9846V       = 0x1a;
	public const ushort PCI_9846VW      = 0x1a;
	//PCIe 98x6 devices
	public const ushort PCIe_9816D      = 0x22;
	public const ushort PCIe_9826D      = 0x23;
	public const ushort PCIe_9846D      = 0x24;
	public const ushort PCIe_9846DW     = 0x24;
	public const ushort PCIe_9816H      = 0x25;
	public const ushort PCIe_9826H      = 0x26;
	public const ushort PCIe_9846H      = 0x27;
	public const ushort PCIe_9846HW     = 0x27;
	public const ushort PCIe_9816V      = 0x28;
	public const ushort PCIe_9826V      = 0x29;
	public const ushort PCIe_9846V      = 0x2a;
	public const ushort PCIe_9846VW     = 0x2a;
  public const ushort PCIe_9842       = 0x30;
  public const ushort PXIe_9848       = 0x32;
  public const ushort PCIe_9852       = 0x33;
  public const ushort PXIe_9852       = 0x34;    	
	//obsolete
	public const ushort PCI_9816        =2;
	public const ushort PCI_9826        =3;
	public const ushort PCI_9846        =4;
	
	public const ushort MAX_CARD        =32;
		
	//Error Number
	public const short NoError                       =0;
	public const short ErrorUnknownCardType         =-1;
	public const short ErrorInvalidCardNumber       =-2;
	public const short ErrorTooManyCardRegistered   =-3;
	public const short ErrorCardNotRegistered       =-4;
	public const short ErrorFuncNotSupport          =-5;
	public const short ErrorInvalidIoChannel        =-6;
	public const short ErrorInvalidAdRange          =-7;
	public const short ErrorContIoNotAllowed        =-8;
	public const short ErrorDiffRangeNotSupport     =-9;
	public const short ErrorLastChannelNotZero      =-10;
	public const short ErrorChannelNotDescending    =-11;
	public const short ErrorChannelNotAscending     =-12;
	public const short ErrorOpenDriverFailed        =-13;
	public const short ErrorOpenEventFailed         =-14;
	public const short ErrorTransferCountTooLarge   =-15;
	public const short ErrorNotDoubleBufferMode     =-16;
	public const short ErrorInvalidSampleRate       =-17;
	public const short ErrorInvalidCounterMode      =-18;
	public const short ErrorInvalidCounter          =-19;
	public const short ErrorInvalidCounterState     =-20;
	public const short ErrorInvalidBinBcdParam      =-21;
	public const short ErrorBadCardType             =-22;
	public const short ErrorInvalidDaRefVoltage     =-23;
	public const short ErrorAdTimeOut               =-24;
	public const short ErrorNoAsyncAI               =-25;
	public const short ErrorNoAsyncAO               =-26;
	public const short ErrorNoAsyncDI               =-27;
	public const short ErrorNoAsyncDO               =-28;
	public const short ErrorNotInputPort            =-29;
	public const short ErrorNotOutputPort           =-30;
	public const short ErrorInvalidDioPort          =-31;
	public const short ErrorInvalidDioLine          =-32;
	public const short ErrorContIoActive            =-33;
	public const short ErrorDblBufModeNotAllowed    =-34;
	public const short ErrorConfigFailed            =-35;
	public const short ErrorInvalidPortDirection    =-36;
	public const short ErrorBeginThreadError        =-37;
	public const short ErrorInvalidPortWidth        =-38;
	public const short ErrorInvalidCtrSource        =-39;
	public const short ErrorOpenFile                =-40;
	public const short ErrorAllocateMemory          =-41;
	public const short ErrorDaVoltageOutOfRange     =-42;
	public const short ErrorDaExtRefNotAllowed      =-43;
	public const short ErrorInvalidBufferID         =-44;
	public const short ErrorInvalidCNTInterval	=-45;
	public const short ErrorReTrigModeNotAllowed    =-46;
	public const short ErrorResetBufferNotAllowed   =-47;
	public const short ErrorAnaTriggerLevel         =-48;
	public const short ErrorDAQEvent		=-49;
	public const short ErrorInvalidDataSize         =-50;
	public const short ErrorOffsetCalibration       =-51;
	public const short ErrorGainCalibration         =-52;
	public const short ErrorCountOutofSDRAMSize     =-53;
	public const short ErrorNotStartTriggerModule   =-54;
	public const short ErrorInvalidRouteLine        =-55;
	public const short ErrorInvalidSignalCode       =-56;
	public const short ErrorInvalidSignalDirection  =-57;
	public const short ErrorTRGOSCalibration        =-58;
	public const short ErrorNoSDRAM                 =-59;
	public const short ErrorIntegrationGain         =-60;
	public const short ErrorAcquisitionTiming       =-61;
	public const short ErrorIntegrationTiming       =-62;
	public const short ErrorInvalidTraceCnt         =-63;
	public const short ErrorTriggerSource           =-64;
	public const short ErrorInvalidTimeBase         =-70;
	public const short ErrorUndefinedParameter	=-71;
	public const short ErrorNotDAQSteppedMode       =-80;
	public const short ErrorBufAddrNotQuadDWordAlignment  = -90;	
	//Error number for calibration API 
	public const short ErrorCalAddress		=-110;
	public const short ErrorInvalidCalBank		=-111;
	//Error number for driver API 
	public const short ErrorConfigIoctl		 =-201;
	public const short ErrorAsyncSetIoctl		 =-202;
	public const short ErrorDBSetIoctl		 =-203;
	public const short ErrorDBHalfReadyIoctl	 =-204;
	public const short ErrorContOPIoctl		 =-205;
	public const short ErrorContStatusIoctl		 =-206;
	public const short ErrorPIOIoctl		 =-207;
	public const short ErrorDIntSetIoctl		 =-208;
	public const short ErrorWaitEvtIoctl		 =-209;
	public const short ErrorOpenEvtIoctl		 =-210;
	public const short ErrorCOSIntSetIoctl		 =-211;
	public const short ErrorMemMapIoctl		 =-212;
	public const short ErrorMemUMapSetIoctl		 =-213;
	public const short ErrorCTRIoctl		 =-214;
	public const short ErrorGetResIoctl		 =-215;
	//Synchronous Mode
	public const ushort SYNCH_OP        =1;
	public const ushort ASYNCH_OP       =2;
	//AD Range
	public const ushort AD_B_10_V       =1;
	public const ushort AD_B_5_V        =2;
	public const ushort AD_B_2_5_V      =3;
	public const ushort AD_B_1_25_V     =4;
	public const ushort AD_B_0_625_V    =5;
	public const ushort AD_B_0_3125_V   =6;
	public const ushort AD_B_0_5_V      =7;
	public const ushort AD_B_0_05_V     =8;
	public const ushort AD_B_0_005_V    =9;
	public const ushort AD_B_1_V       =10;
	public const ushort AD_B_0_1_V     =11;
	public const ushort AD_B_0_01_V    =12;
	public const ushort AD_B_0_001_V   =13;
	public const ushort AD_U_20_V      =14;
	public const ushort AD_U_10_V      =15;
	public const ushort AD_U_5_V       =16;
	public const ushort AD_U_2_5_V     =17;
	public const ushort AD_U_1_25_V    =18;
	public const ushort AD_U_1_V       =19;
	public const ushort AD_U_0_1_V     =20;
	public const ushort AD_U_0_01_V    =21;
	public const ushort AD_U_0_001_V   =22;
	public const ushort AD_B_2_V	   = 23;
	public const ushort AD_B_0_25_V	   = 24;
	public const ushort AD_B_0_2_V	   = 25;
	public const ushort AD_U_4_V	   = 26;
	public const ushort AD_U_2_V	   = 27;
	public const ushort AD_U_0_5_V	   = 28;
	public const ushort AD_U_0_4_V	   = 29;
	public const ushort AD_B_1_5_V	   = 30;
	public const ushort AD_B_0_2145_V  = 31;	
	
	public const short All_Channels   =-1;

	public const ushort WD_AI_ADCONVSRC_TimePacer =0;


	public const ushort WD_AI_TRGSRC_SOFT      =0x00;   
	public const ushort WD_AI_TRGSRC_ANA       =0x01;   
	public const ushort WD_AI_TRGSRC_ExtD      =0x02;   
	public const ushort WD_AI_TRSRC_SSI_1      =0x03;
	public const ushort WD_AI_TRSRC_SSI_2      =0x04;
	public const ushort WD_AI_TRSRC_PXIStar    =0x05; 
	public const ushort WD_AI_TRSRC_PXIeStar   =0x06;	         
	public const ushort WD_AI_TRGMOD_POST      =0x00;   //Post Trigger Mode
	public const ushort WD_AI_TRGMOD_PRE       =0x01;   //Pre-Trigger Mode
	public const ushort WD_AI_TRGMOD_MIDL      =0x02;   //Middle Trigger Mode
	public const ushort WD_AI_TRGMOD_DELAY     =0x03;   //Delay Trigger Mode

	public const ushort WD_AI_TrgPositive      =0x1;
	public const ushort WD_AI_TrgNegative      =0x0;
	
	//obsolete
	public const ushort WD_AI_TRSRC_PXIStart   =0x05;  
	public const ushort WD_AIEvent_Manual      =0x80;   //AI event manual reset

	// define analog trigger Dedicated Channel 
	public const ushort CH0ATRIG		   =0x00;
	public const ushort CH1ATRIG		   =0x01;
	public const ushort CH2ATRIG		   =0x02;
	public const ushort CH3ATRIG		   =0x03;
	public const ushort CH4ATRIG		   =0x04;
	public const ushort CH5ATRIG		   =0x05;
	public const ushort CH6ATRIG		   =0x06;
	public const ushort CH7ATRIG		   =0x07;		
	// Time Base 
	public const ushort WD_ExtTimeBase	   =0x0;
	public const ushort WD_SSITimeBase	   =0x1;
	public const ushort WD_StarTimeBase	   =0x2;
	public const ushort WD_IntTimeBase	   =0x3;
	public const ushort WD_PXI_CLK10	   =0x4;	
	public const ushort WD_PLL_REF_PXICLK10	   =0x4;
	public const ushort WD_PLL_REF_EXT10	   =0x5;
	public const ushort WD_PXIe_CLK100	   =0x6;
	public const ushort WD_PLL_REF_PXIeCLK100  =0x6;
	
	//SSI signal codes
	public const ushort SSI_TIME	   =15;
	public const ushort SSI_TRIG_SRC1   =7;
	public const ushort SSI_TRIG_SRC2   =5;
	public const ushort SSI_TRIG_SRC2_S =5;
	public const ushort SSI_TRIG_SRC2_T =6;
	public const ushort SSI_PRE_DATA_RDY = 0x10;
	// signal lines
	public const ushort PXI_TRIG_0      =0;
	public const ushort PXI_TRIG_1      =1;
	public const ushort PXI_TRIG_2      =2;
	public const ushort PXI_TRIG_3      =3;
	public const ushort PXI_TRIG_4      =4;
	public const ushort PXI_TRIG_5      =5;
	public const ushort PXI_TRIG_6      =6;
	public const ushort PXI_TRIG_7      =7;
	public const ushort PXI_STAR_TRIG   =8;
	public const ushort TRG_IO          =9;
	//obsolete
	public const ushort PXI_START_TRIG  =8;
	
	//SSI cable lines
	public const ushort SSI_LINE_0 = 0;
	public const ushort SSI_LINE_1 = 1;
	public const ushort SSI_LINE_2 = 2;
	public const ushort SSI_LINE_3 = 3;
	public const ushort SSI_LINE_4 = 4;
	public const ushort SSI_LINE_5 = 5;
	public const ushort SSI_LINE_6 = 6;
	public const ushort SSI_LINE_7 = 7;
		
	//Software trigger op code
	public const byte SOFTTRIG_AI = 0x1;
	public const byte SOFTTRIG_AI_OUT = 0x2;
	//DAQ Event type for the event message  
	public const ushort DAQEnd   =0;
	public const ushort DBEvent  =1;
	public const ushort TrigEvent =2;	
	//DAQ advanced mode  
	public const ushort DAQSTEPPED   =0x1;   
	public const ushort RestartEn	 =0x2;
	public const ushort DualBufEn	 =0x4;
	public const ushort ManualSoftTrg =0x40;
	public const ushort DMASTEPPED =0x80;
	public const ushort AI_AVE = 0x8;
	public const ushort AI_AVE_32 = 0x10;	
	//AI channel parameter
  public const ushort AI_RANGE = 0;
  public const ushort AI_IMPEDANCE = 1;
  public const ushort ADC_DITHER =   2;
  public const ushort AI_COUPLING =  3;
  public const ushort ADC_Bandwidth = 4;
 	//AI channel parameter value
  public const ushort IMPEDANCE_50Ohm = 0;
  public const ushort IMPEDANCE_HI = 1;
 	public const ushort ADC_DITHER_DIS = 0;
  public const ushort ADC_DITHER_EN = 1;  
  public const ushort DC_Coupling = 0;
  public const ushort AC_Coupling = 1;    	        
  public const ushort BANDWIDTH_DEVICE_DEFAULT = 0;
  public const ushort BANDWIDTH_20M = 20;    	
	public const ushort BANDWIDTH_100M = 100;    		
	// TrigOUT Channel
	public const ushort AITRIGOUT_CH0  =0;
	public const ushort AITRIGOUT_PXI =2;
	public const ushort AITRIGOUT_PXI_TRIG_0 =2;
	public const ushort AITRIGOUT_PXI_TRIG_1 =3;
	public const ushort AITRIGOUT_PXI_TRIG_2 =4;
	public const ushort AITRIGOUT_PXI_TRIG_3 =5;
	public const ushort AITRIGOUT_PXI_TRIG_4 =6;
	public const ushort AITRIGOUT_PXI_TRIG_5 =7;
	public const ushort AITRIGOUT_PXI_TRIG_6 =8;	
	public const ushort AITRIGOUT_PXI_TRIG_7 =9;	  	
  	//DIO Port Direction
	public const ushort INPUT_PORT  = 1;
	public const ushort OUTPUT_PORT = 2;
	//DIO Line Direction
	public const ushort INPUT_LINE =  1;
	public const ushort OUTPUT_LINE = 2;
	//DIO mode
	public const ushort SDI_En  = 0;
	public const ushort SDI_Dis = 1;
	//Calibration Action
	public const ushort CalLoad = 0;
	public const ushort AutoCal = 1;
	public const ushort CalCopy = 2;  	
	// TrigOUT Config
	public const ushort WD_OutTrgPWidth_50ns  =0;
	public const ushort WD_OutTrgPWidth_100ns =1;
	public const ushort WD_OutTrgPWidth_150ns =2;
	public const ushort WD_OutTrgPWidth_200ns =3;
	public const ushort WD_OutTrgPWidth_500ns =4;
	public const ushort WD_OutTrgPWidth_1us   =5;
	public const ushort WD_OutTrgPWidth_2us   =6;
	public const ushort WD_OutTrgPWidth_5us   =7;
	public const ushort WD_OutTrgPWidth_10us  =8;
	//TrigOUT SRC/POL Config
	public const ushort WD_OutTrgSrcAuto = 0x0;
	public const ushort WD_OutTrgSrcManual = 0x1;
	public const ushort WD_OutTrg_Rising = 0x0;
	public const ushort WD_OutTrg_Fall = 0x10;	
	
	[StructLayout(LayoutKind.Sequential)]
	public struct WD_DEVICE
	{
		public ushort wModuleType;
		public ushort wCardID;
		public ushort geo_addr;
		public ushort Reserved;
		[MarshalAs(UnmanagedType.ByValTStr, SizeConst = 64)] 
		public string dispname;
	};
		
	/*------------------------------------------------------------------
	** PCIS-DASK Function prototype
	------------------------------------------------------------------*/
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Register_Card (ushort CardType, ushort card_num);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Register_Card_By_PXISlot_GA (ushort CardType, ushort ga);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Get_SDRAMSize  (ushort CardNumber, out uint sdramsize);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_SoftTriggerGen(ushort wCardNumber, byte op);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Release_Card  (ushort CardNumber);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_GetActualRate(ushort wCardNumber, bool fdir, double Rate, out uint interval, out double ActualRate);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_GetPXIGeographAddr (ushort wCardNumber, out byte geo_addr);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_GetBaseAddr(ushort wCardNumber, out uint BaseAddr, out uint BaseAddr2);
  [DllImport("WD-Dask.dll")]
  public static extern IntPtr WD_Buffer_Alloc (ushort wCardNumber, uint dwSize);
  [DllImport("WD-Dask.dll")]
  public static extern bool WD_Buffer_Free(ushort wCardNumber, IntPtr buf);
  [DllImport("WD-Dask.dll")]
	public static extern short WD_Device_Scan(IntPtr AvailModules, ushort ncount, out ushort retcnt);
  [DllImport("WD-Dask.dll")]
  public static extern short WD_Device_Scan([MarshalAsAttribute(UnmanagedType.LPArray)] [In, Out] WD_DEVICE[] AvailModuled, ushort ncount, out ushort retcnt); 
  [DllImport("WD-Dask.dll")]
  public static extern short WD_GetFPGAVersion(ushort wCardNumber, out uint version);   
	/*---------------------------------------------------------------------------*/
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_Config (ushort wCardNumber, ushort TimeBase, bool adDutyRestore, ushort ConvSrc, bool doubleEdged, bool AutoResetBuf);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_Trig_Config (ushort wCardNumber, ushort trigMode, ushort trigSrc, ushort trigPol, ushort anaTrigchan, double anaTriglevel, uint postTrigScans, uint preTrigScans, uint trigDelayTicks, uint reTrgCnt);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_OutTrig_Config (ushort wCardNumber, ushort trig_Ch, ushort trig_conf, ushort trig_width);	
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_Set_Mode (ushort wCardNumber, ushort modeCtrl, ushort wIter);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_CH_Config (ushort wCardNumber, short wChannel, ushort wAdRange);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_CH_ChangeParam (ushort wCardNumber, short wChannel, ushort wParam, ushort wValue);	
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_InitialMemoryAllocated (ushort CardNumber, out uint MemSize);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_VoltScale (ushort CardNumber, ushort AdRange, short reading, out double voltage);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_VoltScale32 (ushort CardNumber, ushort AdRange, int reading, out double voltage);	
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContReadChannel (ushort CardNumber, ushort Channel,
					  ushort BufId, uint ReadScans, uint ScanIntrv, uint SampIntrv, ushort SyncMode);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContReadMultiChannels (ushort CardNumber, ushort NumChans, ushort[] Chans,
					  ushort BufId, uint ReadScans, uint ScanIntrv, uint SampIntrv, ushort SyncMode);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContScanChannels (ushort CardNumber, ushort Channel,
					  ushort BufId, uint ReadScans, uint ScanIntrv, uint SampIntrv, ushort SyncMode);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContReadChannelToFile (ushort CardNumber, ushort Channel, ushort BufId,
					  string FileName, uint ReadScans, uint ScanIntrv, uint SampIntrv, ushort SyncMode);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContReadMultiChannelsToFile (ushort CardNumber, ushort NumChans, ushort[] Chans,
					  ushort BufId, string FileName, uint ReadScans, uint ScanIntrv, uint SampIntrv, ushort SyncMode);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContScanChannelsToFile (ushort CardNumber, ushort Channel, ushort BufId,
					  string FileName, uint ReadScans, uint ScanIntrv, uint SampIntrv, ushort SyncMode);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContStatus (ushort CardNumber, out uint Status);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContVScale (ushort wCardNumber, ushort adRange, short[] readingArray,double[] voltageArray, int count);	
	[DllImport("WD-Dask.dll")]
  public static extern short WD_AI_ContVScale(ushort wCardNumber, ushort adRange, IntPtr readingArray, double[] voltageArray, int count);
  [DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContVScale (ushort wCardNumber, ushort adRange, IntPtr readingArray, IntPtr voltageArray, int count);
  [DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContVScaleEx (ushort wCardNumber, ushort adRange, ushort width, int[] readingArray, double[] voltageArray, int count);	
	[DllImport("WD-Dask.dll")]
  public static extern short WD_AI_ContVScaleEx(ushort wCardNumber, ushort adRange, ushort width, IntPtr readingArray, double[] voltageArray, int count);
  [DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContVScaleEx (ushort wCardNumber, ushort adRange, ushort width, IntPtr readingArray, IntPtr voltageArray, int count);
		
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncCheck (ushort CardNumber, out byte Stopped, out uint AccessCnt);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncClear (ushort CardNumber, out uint StartPos, out uint AccessCnt);
  [DllImport("WD-Dask.dll")]
  public static extern short WD_AI_AsyncClearEx(ushort CardNumber, out uint StartPos, out uint AccessCnt, int NoWait);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncDblBufferHalfReady (ushort CardNumber, out char HalfReady, out char StopFlag);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncDblBufferMode (ushort CardNumber, bool Enable);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncDblBufferToFile (ushort CardNumber);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContBufferSetup (ushort wCardNumber, short[] pwBuffer, uint dwReadCount, out ushort BufferId);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContBufferSetup (ushort wCardNumber, IntPtr pwBuffer, uint dwReadCount, out ushort BufferId);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContBufferSetup32 (ushort wCardNumber, int[] pwBuffer, uint dwReadCount, out ushort BufferId);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContBufferSetup32 (ushort wCardNumber, IntPtr pwBuffer, uint dwReadCount, out ushort BufferId);	
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ContBufferReset (ushort wCardNumber);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_DMA_Transfer (ushort wCardNumber, ushort BufId);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_ConvertCheck (ushort wCardNumber, out char bStopped);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncReStartNextReady (ushort wCardNumber, out char bReady, out char StopFlag, out ushort RdyDaqCnt);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_EventCallBack(ushort wCardNumber, short mode, short EventType, MulticastDelegate callbackAddr);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_SetTimeout (ushort wCardNumber, uint msec);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncReTrigNextReady (ushort wCardNumber, out byte trgReady, out byte StopFlag, out uint RdyTrigCnt);	
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncDblBufferHandled (ushort wCardNumber);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_AI_AsyncDblBufferOverrun (ushort wCardNumber, ushort op, out ushort overrunFlag);
	
	[DllImport("WD-Dask.dll")]
	public static extern short WD_SSI_SourceConn (ushort wCardNumber, ushort sigCode);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_SSI_SourceDisConn (ushort wCardNumber, ushort sigCode);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_SSI_SourceClear (ushort wCardNumber);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Route_Signal (ushort wCardNumber, ushort signal, ushort Line, ushort dir);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Signal_DisConn (ushort wCardNumber, ushort signal, ushort Line);

	[DllImport("WD-Dask.dll")]
	public static extern short WD_AD_Auto_Calibration_ALL(ushort wCardNumber);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_EEPROM_CAL_Constant_Update(ushort wCardNumber, ushort bank);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Load_CAL_Data(ushort wCardNumber, ushort bank);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Set_Default_Load_Area(ushort wCardNumber, ushort bank);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_Get_Default_Load_Area(ushort wCardNumber);		
	/*---------------------------------------------------------------------------*/
	[DllImport("WD-Dask.dll")]
	public static extern short WD_DI_ReadLine (ushort CardNumber, ushort Port, ushort Line, out ushort State);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_DI_ReadPort (ushort CardNumber, ushort Port, out uint Value);
	/*---------------------------------------------------------------------------*/
	[DllImport("WD-Dask.dll")]
	public static extern short WD_DO_WriteLine (ushort CardNumber, ushort Port, ushort Line, ushort Value);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_DO_WritePort (ushort CardNumber, ushort Port, uint Value);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_DO_ReadLine (ushort CardNumber, ushort Port, ushort Line, out ushort Value);
	[DllImport("WD-Dask.dll")]
	public static extern short WD_DO_ReadPort (ushort CardNumber, ushort Port, out uint Value);
	/*---------------------------------------------------------------------------*/
	[DllImport("WD-Dask.dll")]
	public static extern short WD_DIO_PortConfig (ushort CardNumber, ushort Port, ushort mode, ushort Direction);
	[DllImport("WD-Dask.dll")]	
	public static extern short WD_DIO_LineConfig (ushort CardNumber, ushort Port, uint Line, ushort Direction);
	[DllImport("WD-Dask.dll")]	
	public static extern short WD_DIO_LinesConfig (ushort CardNumber, ushort Port, ushort mode, uint Linesdirmap);			
}