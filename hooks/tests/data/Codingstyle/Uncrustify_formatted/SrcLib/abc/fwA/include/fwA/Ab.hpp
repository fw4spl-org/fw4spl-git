/* ***** BEGIN LICENSE BLOCK *****
 * FW4SPL - Copyright (C) IRCAD, 2009-2999.
 * Distributed under the terms of the GNU Lesser General Public License (LGPL) as
 * published by the Free Software Foundation.
 * ****** END LICENSE BLOCK ****** */

#ifndef __FWA_AB_HPP__
#define __FWA_AB_HPP__

namespace fwA
{

class AB_CLASS_API Ab
{

public:

    //------------------------------------------------------------------------------

    AB_API inline bool doSomething()
    {
        return this->doSomethingPrivately();
    }

private:

    //------------------------------------------------------------------------------

    inline bool doSomethingPrivately()
    {
        return true;
    }
};

} // namespace fwA

#endif // __FWA_AB_HPP__
