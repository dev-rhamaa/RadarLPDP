
#ifndef		_DAQHEADER_H
#define		_DAQHEADER_H

/*==========================================

              Map of DAQ File
		+-------------------------+
		|                         |
		|	      Header	      |
		|                         | 
		+-------------------------+
		|      ChannelRange       |
		|       (Optional)        |
		+-------------------------+
		|                         |
		|         DAQ data        |
		|                         |
		|                         |
		+-------------------------+

============================================*/
#pragma pack( push, before_include )

#pragma pack(1)

//----- size is 60 bytes
typedef	struct	_DAQFILE_HEADER  {
		char	ID[10];				//ex "ADLinkDAQ1"
		short	card_type;			//Pci7250, Pci9112...(include DG, HR, HG)
		short	num_of_channel;		//1, 2,...
        unsigned char	channel_no;	//used only num_of_channel is 1
		long	num_of_scan;
		short	data_width;			//0: 8 bits, 1: 16 bits, 2: 32 bits
		short	channel_order;		//0: 0-1-2-3, 1: 3-2-1-0, 2: custom
		short	ad_range;			
		double	scan_rate;
		short	num_of_channel_range;
		char	start_date[8];		//"12/31/99"
		char	start_time[8];		//"18:30:25"
		char	start_millisec[3];	//"360"
		char	reserved[6];
}	DAQFileHeader;


typedef	struct	_CHANNEL_RANGE  {
	unsigned char	channel;
	unsigned char	range;
}	DAQChannelRange;


/*----- ADLink PCI Card Type
#define PCI_6208V       1
#define PCI_6208A       2
#define PCI_6308V       3
#define PCI_6308A       4
#define PCI_7200        5
#define PCI_7230        6
#define PCI_7233        7
#define PCI_7234        8
#define PCI_7248        9
#define PCI_7249        10
#define PCI_7250        11
#define PCI_7252        12
#define PCI_7296        13
#define PCI_7300A_RevA  14
#define PCI_7300A_RevB  15
#define PCI_7432        16
#define PCI_7433        17
#define PCI_7434        18
#define PCI_8554        19
#define PCI_9111DG      20
#define PCI_9111HR      21
#define PCI_9112        22
#define PCI_9113        23
#define PCI_9114DG      24
#define PCI_9114HG      25
#define PCI_9118DG      26
#define PCI_9118HG      27
#define PCI_9118HR      28
#define PCI_9810        29
#define PCI_9812        30
#define PCI_7396        31
*/

//---- AD Range
//	AD_B_10_V       1
//	AD_B_5_V        2
//	AD_B_2_5_V      3
//	AD_B_1_25_V     4
//	AD_B_0_625_V    5
//	AD_B_0_3125_V   6
//	AD_B_0_5_V      7
//	AD_B_0_05_V     8
//	AD_B_0_005_V    9
//	AD_B_1_V       10
//	AD_B_0_1_V     11
//	AD_B_0_01_V    12
//	AD_B_0_001_V   13
//	AD_U_20_V      14
//	AD_U_10_V      15
//	AD_U_5_V       16
//	AD_U_2_5_V     17
//	AD_U_1_25_V    18
//	AD_U_1_V       19
//	AD_U_0_1_V     20
//	AD_U_0_01_V    21
//	AD_U_0_001_V   22

#pragma pack( pop, before_include )

#endif		//_DAQHEADER_H
