from scipy import optimize
def func(x):

    return x[0]*x[1]

bnds=((0,100),(0,5))

cons=({'type':'eq','fun':lambda x:x[0]+x[1]-5})
x0=[0,0]
res= optimize.minimize(func,x0,method='SLSQP',bounds=bnds,constraints=cons)
print(res)