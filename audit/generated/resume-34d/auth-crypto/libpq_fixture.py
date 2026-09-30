"""Minimal ctypes libpq fixture adapter, actual Unix socket PostgreSQL, no mock."""
import ctypes
class DB:
 def __init__(self,name):
  l=self.l=ctypes.CDLL('/tmp/kcml-pg18/lib/libpq.so');P=ctypes.c_void_p;S=ctypes.c_char_p;I=ctypes.c_int
  for n,args,rest in [('PQconnectdb',[S],P),('PQstatus',[P],I),('PQtransactionStatus',[P],I),('PQerrorMessage',[P],S),('PQexec',[P,S],P),('PQresultStatus',[P],I),('PQntuples',[P],I),('PQnfields',[P],I),('PQgetvalue',[P,I,I],S),('PQgetisnull',[P,I,I],I),('PQclear',[P],None),('PQfinish',[P],None)]:
   f=getattr(l,n);f.argtypes=args;f.restype=rest
  self.c=l.PQconnectdb(f'host=/tmp/kcml-pg18-socket port=55432 dbname={name}'.encode())
  if l.PQstatus(self.c):raise RuntimeError(l.PQerrorMessage(self.c).decode())
 def query(self,sql):
  l=self.l;r=l.PQexec(self.c,sql.encode())
  try:
   if l.PQresultStatus(r) not in (1,2):raise RuntimeError(l.PQerrorMessage(self.c).decode())
   return [[None if l.PQgetisnull(r,i,j) else l.PQgetvalue(r,i,j).decode() for j in range(l.PQnfields(r))]for i in range(l.PQntuples(r))]
  finally:l.PQclear(r)
 def transaction_status(self):return self.l.PQtransactionStatus(self.c)
 def close(self):self.l.PQfinish(self.c)
def lit(x):return "'"+str(x).replace("'","''")+"'"
