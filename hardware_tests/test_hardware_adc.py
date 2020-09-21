import mcp3008
adc = mcp3008.MCP3008()
print(adc.read([mcp3008.CH0])) # prints raw data [CH0]
adc.close()
